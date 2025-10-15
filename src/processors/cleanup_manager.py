import asyncio
from datetime import datetime, timezone, timedelta
from src.core.interfaces import DatabaseInterface
from src.core.config import logger

# ---------------------------------------------------
# Cleanup Management Component
# ---------------------------------------------------

class CleanupManager:
    """Handles cleanup of old data using time-based TTL for array-based track storage"""
    
    def __init__(self, database: DatabaseInterface, config=None):
        self.database = database
        self.config = config

    async def cleanup_old_data_by_time(self, current_time: datetime = None) -> None:
        """
        Delete nodes and relationships older than rolling window (time-based TTL)
        
        IMPORTANT: USD Schema Nodes are NEVER cleaned up:
        - Scene_Descriptor (singleton with venue data)
        - CameraConfig (6 camera configurations)
        - FusedPlayer (25 player current states)
        - FusionBall3D (ball current state)
        
        These nodes persist indefinitely and represent the current game state.
        """
        if current_time is None:
            current_time = datetime.now(timezone.utc)
        
        # Get rolling window from config
        rolling_window_seconds = self.config.rolling_window_seconds if self.config else 30
        cutoff_time = current_time - timedelta(seconds=rolling_window_seconds)
        cutoff_timestamp = cutoff_time.isoformat().replace('+00:00', 'Z')

        logger.debug(f"Cleaning up all data older than {cutoff_timestamp} (rolling window: {rolling_window_seconds}s)")

        # Retry logic for transaction conflicts - common in high-throughput systems
        max_retries = 3
        base_delay = self.config.cleanup_base_delay if self.config else 0.1
        
        for attempt in range(max_retries):
            try:
                # Verify Scene_Descriptor exists before cleanup (paranoid safety check)
                try:
                    cursor = self.database.connection.cursor()
                    cursor.execute("MATCH (sd:Scene_Descriptor) RETURN count(sd)")
                    sd_count = cursor.fetchall()[0][0] if cursor.fetchall() else 0
                    if sd_count == 0:
                        logger.warning("⚠️  Scene_Descriptor missing before cleanup! Cleanup may have deleted it previously.")
                except Exception as e:
                    logger.debug(f"Could not verify Scene_Descriptor: {e}")
                
                # More aggressive cleanup with larger limits to actually clean up data
                # NOTE: USD nodes (Scene_Descriptor, CameraConfig, FusedPlayer, FusionBall3D) 
                # are NOT included here - they persist indefinitely
                cleanup_statements = [
                    # Clean up track nodes first (most numerous) - no limits for complete cleanup
                    "MATCH (pt:PlayerTrack) WHERE pt.last_updated < $cutoff_timestamp DETACH DELETE pt",
                    "MATCH (bt:BallTrack) WHERE bt.last_updated < $cutoff_timestamp DETACH DELETE bt",
                    # Clean up PTZ and CamParams nodes - no limits
                    "MATCH (s:PTZState) WHERE s.timestamp < $cutoff_timestamp DETACH DELETE s",
                    "MATCH (cp:CamParams) WHERE cp.timestamp < $cutoff_timestamp DETACH DELETE cp",
                    # Clean up Frame and Camera nodes - no limits
                    "MATCH (f:Frame) WHERE f.timestamp < $cutoff_timestamp DETACH DELETE f",
                    "MATCH (c:Camera) WHERE c.last_active_timestamp < $cutoff_timestamp DETACH DELETE c"
                ]
                
                # Execute cleanup statements with timeout protection
                for i, query in enumerate(cleanup_statements):
                    try:
                        # Add timeout to prevent long-running queries
                        result = await asyncio.wait_for(
                            self.database.execute_query(query, {"cutoff_timestamp": cutoff_timestamp}),
                            timeout=10.0  # 10 second timeout per query for complete cleanup
                        )
                        logger.debug(f"Cleanup statement {i+1} completed - deleted nodes")
                    except asyncio.TimeoutError:
                        logger.warning(f"Cleanup statement {i+1} timed out, skipping")
                        break  # Stop cleanup if any query times out
                    except Exception as e:
                        logger.error(f"Cleanup statement {i+1} failed: {e}")
                        break  # Stop cleanup if any query fails

                # Verify Scene_Descriptor still exists after cleanup (paranoid safety check)
                try:
                    cursor = self.database.connection.cursor()
                    cursor.execute("MATCH (sd:Scene_Descriptor) RETURN count(sd)")
                    result = cursor.fetchall()
                    sd_count = result[0][0] if result and result[0] else 0
                    if sd_count == 0:
                        logger.error("❌ CRITICAL: Scene_Descriptor was DELETED during cleanup!")
                        logger.error("   Cleanup queries should NEVER delete Scene_Descriptor!")
                        logger.error("   This indicates a bug in the cleanup logic.")
                        logger.error("   Please run: python init_usd_scene.py")
                        # Note: Cannot auto-recover here since we're in cleanup context
                        # User must manually run init_usd_scene.py
                except Exception as e:
                    logger.debug(f"Could not verify Scene_Descriptor after cleanup: {e}")
                
                logger.debug(f"Time-based cleanup completed successfully for data older than {cutoff_timestamp}")
                return  # Success - exit retry loop
                
            except Exception as e:
                error_msg = str(e).lower()
                if "conflicting transaction" in error_msg or "cannot resolve" in error_msg:
                    if attempt < max_retries - 1:
                        # Exponential backoff for transaction conflicts
                        delay = base_delay * (2 ** attempt)
                        logger.warning(f"Transaction conflict during cleanup (attempt {attempt + 1}/{max_retries}), retrying in {delay:.2f}s...")
                        await asyncio.sleep(delay)
                        continue
                    else:
                        logger.error(f"Cleanup failed after {max_retries} attempts due to transaction conflicts. This may indicate high system load.")
                else:
                    logger.error(f"Error during cleanup transaction: {e}")
                    return  # Non-retryable error

    # Legacy method for backward compatibility
    async def cleanup_old_ticks(self, current_tick: int, rolling_window: int) -> None:
        """Legacy tick-based cleanup (deprecated: use cleanup_old_data_by_time)"""
        logger.warning("Using deprecated tick-based cleanup. Consider migrating to time-based TTL.")
        # Convert tick-based to time-based for backward compatibility
        # This is a rough approximation - in practice, you'd want to track the relationship
        # between ticks and time more accurately
        current_time = datetime.now(timezone.utc)
        await self.cleanup_old_data_by_time(current_time)

    async def cleanup_specific_entity_by_time(self, entity_type: str, current_time: datetime = None) -> None:
        """Cleanup specific entity type using time-based TTL"""
        if current_time is None:
            current_time = datetime.now(timezone.utc)
        
        # Get rolling window from config
        rolling_window_seconds = self.config.rolling_window_seconds if self.config else 30
        cutoff_time = current_time - timedelta(seconds=rolling_window_seconds)
        cutoff_timestamp = cutoff_time.isoformat().replace('+00:00', 'Z')

        entity_queries = {
            "Frame": "MATCH (f:Frame) WHERE f.timestamp < $cutoff_timestamp DETACH DELETE f",
            "PlayerTrack": "MATCH (pt:PlayerTrack) WHERE pt.last_updated < $cutoff_timestamp DETACH DELETE pt",
            "BallTrack": "MATCH (bt:BallTrack) WHERE bt.last_updated < $cutoff_timestamp DETACH DELETE bt",
            "PTZState": "MATCH (s:PTZState) WHERE s.timestamp < $cutoff_timestamp DETACH DELETE s",
            "CamParams": "MATCH (cp:CamParams) WHERE cp.timestamp < $cutoff_timestamp DETACH DELETE cp",
            "Camera": "MATCH (c:Camera) WHERE c.last_active_timestamp < $cutoff_timestamp DETACH DELETE c"
        }

        query = entity_queries.get(entity_type)
        if not query:
            logger.warning(f"Unknown entity type for cleanup: {entity_type}")
            return

        try:
            # Use proper transaction context
            async with self.database.transaction() as transaction:
                await transaction.execute_query(query, {"cutoff_timestamp": cutoff_timestamp})
            logger.debug(f"Time-based cleanup completed for {entity_type} entities older than {cutoff_timestamp}")
        except Exception as e:
            logger.error(f"Error during {entity_type} time-based cleanup: {e}")

    # Legacy method for backward compatibility
    async def cleanup_specific_entity(self, entity_type: str, current_tick: int, rolling_window: int) -> None:
        """Legacy tick-based cleanup for specific entity (deprecated: use cleanup_specific_entity_by_time)"""
        logger.warning("Using deprecated tick-based cleanup for specific entity. Consider migrating to time-based TTL.")
        current_time = datetime.now(timezone.utc)
        await self.cleanup_specific_entity_by_time(entity_type, current_time)

    async def get_cleanup_stats_by_time(self, current_time: datetime = None) -> dict:
        """Get statistics about data that would be cleaned up using time-based TTL"""
        if current_time is None:
            current_time = datetime.now(timezone.utc)
        
        # Get rolling window from config
        rolling_window_seconds = self.config.rolling_window_seconds if self.config else 30
        cutoff_time = current_time - timedelta(seconds=rolling_window_seconds)
        cutoff_timestamp = cutoff_time.isoformat().replace('+00:00', 'Z')

        queries = {
            "frames": "MATCH (f:Frame) WHERE f.timestamp < $cutoff_timestamp RETURN count(f) as count",
            "player_tracks": "MATCH (pt:PlayerTrack) WHERE pt.last_updated < $cutoff_timestamp RETURN count(pt) as count",
            "ball_tracks": "MATCH (bt:BallTrack) WHERE bt.last_updated < $cutoff_timestamp RETURN count(bt) as count",
            "ptz_states": "MATCH (s:PTZState) WHERE s.timestamp < $cutoff_timestamp RETURN count(s) as count",
            "cam_params": "MATCH (cp:CamParams) WHERE cp.timestamp < $cutoff_timestamp RETURN count(cp) as count",
            "cameras": "MATCH (c:Camera) WHERE c.last_active_timestamp < $cutoff_timestamp RETURN count(c) as count"
        }

        stats = {}
        
        try:
            for entity, query in queries.items():
                result = await self.database.execute_query(query, {"cutoff_timestamp": cutoff_timestamp})
                
                count = 0
                if result and len(result) > 0:
                    count = result[0][0] if result[0] else 0
                stats[entity] = count
        except Exception as e:
            logger.error(f"Error getting time-based cleanup stats: {e}")
            stats = {entity: -1 for entity in queries.keys()}  # -1 indicates error

        return stats

    async def cleanup_old_data_by_time_aggressive(self, current_time: datetime = None) -> None:
        """Aggressive cleanup for high-volume track data scenarios"""
        if current_time is None:
            current_time = datetime.now(timezone.utc)
        
        # Shorter rolling window for aggressive cleanup
        rolling_window_seconds = 30  # Extended window for track data
        cutoff_time = current_time - timedelta(seconds=rolling_window_seconds)
        cutoff_timestamp = cutoff_time.isoformat().replace('+00:00', 'Z')

        logger.info(f"Aggressive cleanup: removing data older than {cutoff_timestamp} (30s window)")

        # Prioritize track cleanup first (most numerous with detection data)
        cleanup_priority = [
            "MATCH (pt:PlayerTrack) WHERE pt.last_updated < $cutoff_timestamp DETACH DELETE pt",
            "MATCH (bt:BallTrack) WHERE bt.last_updated < $cutoff_timestamp DETACH DELETE bt", 
            "MATCH (s:PTZState) WHERE s.timestamp < $cutoff_timestamp DETACH DELETE s",
            "MATCH (cp:CamParams) WHERE cp.timestamp < $cutoff_timestamp DETACH DELETE cp",
            "MATCH (f:Frame) WHERE f.timestamp < $cutoff_timestamp DETACH DELETE f",
            "MATCH (c:Camera) WHERE c.last_active_timestamp < $cutoff_timestamp DETACH DELETE c"
        ]
        
        try:
            async with self.database.transaction() as transaction:
                for query in cleanup_priority:
                    await transaction.execute_query(query, {"cutoff_timestamp": cutoff_timestamp})
            logger.info("Aggressive cleanup completed successfully")
        except Exception as e:
            logger.error(f"Error during aggressive cleanup: {e}")

    # Legacy method for backward compatibility
    async def get_cleanup_stats(self, rolling_window: int) -> dict:
        """Legacy tick-based cleanup stats (deprecated: use get_cleanup_stats_by_time)"""
        logger.warning("Using deprecated tick-based cleanup stats. Consider migrating to time-based TTL.")
        current_time = datetime.now(timezone.utc)
        return await self.get_cleanup_stats_by_time(current_time) 