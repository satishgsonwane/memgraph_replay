from typing import Dict, List, Any
from src.core.interfaces import DatabaseInterface
from src.core.config import logger

# ---------------------------------------------------
# Query Execution Component
# ---------------------------------------------------

class QueryExecutor:
    """Handles database query building and execution"""
    
    def __init__(self, database: DatabaseInterface):
        self.database = database

    async def execute_queries(self, batch_groups: Dict[str, list]) -> None:
        """Execute all batch queries with connection pooling for sub-10ms P95 latency."""
        # Add diagnostic logging for large batches
        total_items = sum(len(rows) for rows in batch_groups.values())
        if total_items > 200:
            logger.debug(f"Executing large query batch: {total_items} items across {len(batch_groups)} entity types")
        
        # Process in order: Frame and Camera first, then track entities, then PTZState and CamParams, finally FusionBall3D and USD nodes
        # Node types as per diagram: Frame, Camera, PlayerTrack, BallTrack, PTZState, CamParams, FusionBall3D
        # USD nodes: CameraConfigUpdate, FusedPlayer (no Scene_Descriptor here - initialized once on startup)
        # Persistent nodes: Intent (linked to CameraConfig, no TTL)
        processing_order = ["Frame", "Camera", "PlayerTrack", "BallTrack", "PTZState", "CamParams", "CameraConfigUpdate", "FusionBall3D", "FusedPlayer", "Intent"]
        
        for batch_type in processing_order:
            rows = batch_groups.get(batch_type, [])
            if not rows:
                continue

            if batch_type == "Frame":
                # Keep MERGE for Frame nodes since they may be referenced across batches
                # Use pooled connection for high performance
                if hasattr(self.database, 'execute_query_pooled'):
                    await self.database.execute_query_pooled("""
                        UNWIND $rows AS row
                        MERGE (f:Frame {tickID: row.tickID})
                        SET f.timestamp = row.timestamp
                    """, {"rows": rows})
                else:
                    await self.database.execute_query("""
                        UNWIND $rows AS row
                        MERGE (f:Frame {tickID: row.tickID})
                        SET f.timestamp = row.timestamp
                    """, {"rows": rows})

            elif batch_type == "Camera":
                # Create Camera nodes as per diagram
                await self.database.execute_query("""
                    UNWIND $rows AS row
                    MERGE (c:Camera {cameraID: row.cameraID})
                    SET c.last_active_tick = row.tickID,
                        c.timestamp = row.timestamp,
                        c.last_active_timestamp = row.last_active_timestamp
                """, {"rows": rows})

            elif batch_type == "PlayerTrack":
                # Create PlayerTrack nodes with detection data as per diagram
                await self.database.execute_query("""
                    UNWIND $rows AS row
                    // Create PlayerTrack with detection data (one node per detection)
                    CREATE (pt:PlayerTrack {
                        track_id: row.track_id,
                        tickID: row.current_tick,
                        timestamp: row.timestamp,
                        category: row.category,
                        world_x: row.world_x,
                        world_y: row.world_y,
                        confidence: row.confidence,
                        bbox: row.bbox,
                        transform_PAN: row.transform_PAN,
                        transform_TILT: row.transform_TILT,
                        dist: row.dist,
                        ray_origin: row.ray_origin,
                        ray_world_space_dir: row.ray_world_space_dir,
                        last_updated: row.timestamp
                    })
                    
                    // Create relationships as per diagram
                    WITH pt, row
                    MERGE (f:Frame {tickID: row.current_tick})
                    CREATE (f)-[:HAS_ACTIVE_TRACK]->(pt)
                    
                    WITH pt, row
                    MERGE (c:Camera {cameraID: row.cameraID})
                    CREATE (c)-[:TRACKS_PLAYER]->(pt)
                """, {"rows": rows})

            elif batch_type == "BallTrack":
                # Create BallTrack nodes with detection data as per diagram
                query = """
                    UNWIND $rows AS row
                    // Create BallTrack with detection data (one node per detection)
                    CREATE (bt:BallTrack {
                        track_id: row.track_id,
                        tickID: row.current_tick,
                        timestamp: row.timestamp,
                        world_x: row.world_x,
                        world_y: row.world_y,
                        confidence: row.confidence,
                        bbox: row.bbox,
                        transform_PAN: row.transform_PAN,
                        transform_TILT: row.transform_TILT,
                        dist: row.dist,
                        phi: row.phi,
                        velocity: row.velocity,
                        velocity_x: row.velocity_x,
                        velocity_y: row.velocity_y,
                        velocity_direction: row.velocity_direction,
                        movement_score: row.movement_score,
                        is_best: row.is_best,
                        last_updated: row.timestamp
                    })
                    
                    // Set optional properties only if they are not null
                    WITH bt, row
                    FOREACH (value IN CASE WHEN row.id IS NOT NULL THEN [row.id] ELSE [] END |
                        SET bt.id = value
                    )
                    FOREACH (value IN CASE WHEN row.id_score IS NOT NULL THEN [row.id_score] ELSE [] END |
                        SET bt.id_score = value
                    )
                    FOREACH (value IN CASE WHEN row.dist_score IS NOT NULL THEN [row.dist_score] ELSE [] END |
                        SET bt.dist_score = value
                    )
                    FOREACH (value IN CASE WHEN row.ray_origin IS NOT NULL THEN [row.ray_origin] ELSE [] END |
                        SET bt.ray_origin = value
                    )
                    FOREACH (value IN CASE WHEN row.ray_world_space_dir IS NOT NULL THEN [row.ray_world_space_dir] ELSE [] END |
                        SET bt.ray_world_space_dir = value
                    )
                    
                    // Create relationships as per diagram
                    WITH bt, row
                    MERGE (f:Frame {tickID: row.current_tick})
                    CREATE (f)-[:HAS_ACTIVE_TRACK]->(bt)
                    
                    WITH bt, row
                    MERGE (c:Camera {cameraID: row.cameraID})
                    CREATE (c)-[:TRACKS_BALL]->(bt)
                """
                logger.debug(f"Executing BallTrack query for {len(rows)} rows")
                try:
                    await self.database.execute_query(query, {"rows": rows})
                except Exception as e:
                    logger.error(f"BallTrack query failed: {e}")
                    logger.error(f"Query: {query}")
                    logger.error(f"Sample row data: {rows[0] if rows else 'No rows'}")
                    raise

            elif batch_type == "PTZState":
                # Create PTZState nodes with relationships as per diagram
                await self.database.execute_query("""
                    UNWIND $rows AS row
                    CREATE (s:PTZState {
                        stateID: row.stateID,
                        cameraID: row.cameraID,
                        panposition: row.panposition,
                        tiltposition: row.tiltposition,
                        rollposition: row.rollposition,
                        pansetpoint: row.pansetpoint,
                        tiltsetpoint: row.tiltsetpoint,
                        zoomsetpoint: row.zoomsetpoint,
                        panpower: row.panpower,
                        tiltpower: row.tiltpower,
                        rollpower: row.rollpower,
                        pan: row.pan,
                        tilt: row.tilt,
                        zoomspeed: row.zoomspeed,
                        zoomposition: row.zoomposition,
                        focusposition: row.focusposition,
                        timestamp: row.timestamp,
                        last_updated: row.timestamp
                    })
                    WITH s, row
                    FOREACH (tickID IN CASE WHEN row.tickID IS NOT NULL THEN [row.tickID] ELSE [] END |
                        SET s.tickID = tickID
                    )
                    
                    // Create relationships as per diagram
                    WITH s, row
                    FOREACH (tickID IN CASE WHEN row.tickID IS NOT NULL THEN [row.tickID] ELSE [] END |
                        MERGE (f:Frame {tickID: tickID})
                        CREATE (f)-[:HAS_PTZ_STATE]->(s)
                    )
                    
                    WITH s, row
                    MERGE (c:Camera {cameraID: row.cameraID})
                    CREATE (c)-[:HAS_PTZ_STATE]->(s)
                """, {"rows": rows})

            elif batch_type == "CamParams":
                # Create CamParams nodes with relationships as per diagram
                await self.database.execute_query("""
                    UNWIND $rows AS row
                    CREATE (cp:CamParams {
                        paramsID: row.paramsID,
                        cameraID: row.cameraID,
                        intrinsic: row.intrinsic,
                        rotation: row.rotation,
                        translation: row.translation,
                        timestamp: row.timestamp,
                        last_updated: row.timestamp
                    })
                    WITH cp, row
                    FOREACH (tickID IN CASE WHEN row.tickID IS NOT NULL THEN [row.tickID] ELSE [] END |
                        SET cp.tickID = tickID
                    )
                    
                    // Create relationships as per diagram
                    WITH cp, row
                    FOREACH (tickID IN CASE WHEN row.tickID IS NOT NULL THEN [row.tickID] ELSE [] END |
                        MERGE (f:Frame {tickID: tickID})
                        CREATE (f)-[:HAS_CAM_PARAMS]->(cp)
                    )
                    
                    WITH cp, row
                    MERGE (c:Camera {cameraID: row.cameraID})
                    CREATE (c)-[:HAS_CAM_PARAMS]->(cp)
                """, {"rows": rows})

            elif batch_type == "FusionBall3D":
                # MERGE pattern: Always update the single FusionBall3D node (latest data only)
                # This is a singleton entity - no historical tracking, no tickID, no TTL needed
                await self.database.execute_query("""
                    UNWIND $rows AS row
                    MERGE (fb:FusionBall3D {id: 'singleton'})
                    SET fb.timestamp = row.timestamp,
                        fb.`3dposition` = row.position_world,
                        fb.velocity_mps = row.velocity_mps,
                        fb.status = row.status,
                        fb.fusion_method = row.fusion_method,
                        fb.kalman_filtered = row.kalman_filtered,
                        fb.smooth_2d = row.smooth_2d,
                        fb.camera_ready = row.camera_ready,
                        fb.last_updated = row.timestamp
                """, {"rows": rows})
                
                # Create relationship to Scene_Descriptor in a separate query to ensure it exists
                try:
                    await self.database.execute_query("""
                        MATCH (fb:FusionBall3D {id: 'singleton'})
                        MATCH (sd:Scene_Descriptor)
                        MERGE (sd)-[:HAS_BALL]->(fb)
                    """)
                except Exception as e:
                    logger.debug(f"Could not create HAS_BALL relationship (Scene_Descriptor may not exist yet): {e}")
                
                logger.debug(f"Updated FusionBall3D singleton with latest data ({len(rows)} update(s))")
            
            elif batch_type == "CameraConfigUpdate":
                # Update CameraConfig nodes with gimbal position and camera parameters from all_tracks
                # Uses orjson to serialize nested dicts
                import orjson
                for row in rows:
                    gimbal_json = orjson.dumps(row.get("gimbal_position", {})).decode('utf-8')
                    params_json = orjson.dumps(row.get("camera_parameters", {})).decode('utf-8')
                    
                    await self.database.execute_query("""
                        MERGE (cc:CameraConfig {cameraID: $cameraID})
                        SET cc.gimbal_position = $gimbal_position,
                            cc.camera_parameters = $camera_parameters,
                            cc.last_updated = $timestamp
                    """, {
                        "cameraID": row.get("cameraID"),
                        "gimbal_position": gimbal_json,
                        "camera_parameters": params_json,
                        "timestamp": row.get("timestamp")
                    })
                logger.debug(f"Updated {len(rows)} CameraConfig nodes with gimbal/params")
            
            elif batch_type == "FusedPlayer":
                # MERGE pattern: Update FusedPlayer nodes with latest position and velocity
                # Links to Scene_Descriptor via HAS_PLAYER relationship
                await self.database.execute_query("""
                    UNWIND $rows AS row
                    MERGE (fp:FusedPlayer {id: row.id})
                    SET fp.x = row.x,
                        fp.y = row.y,
                        fp.z = row.z,
                        fp.vel_x = row.vel_x,
                        fp.vel_y = row.vel_y,
                        fp.status = row.status,
                        fp.category = row.category,
                        fp.team = row.team,
                        fp.last_updated = row.timestamp
                """, {"rows": rows})
                
                # Create relationships to Scene_Descriptor in a separate query to ensure it exists
                # MERGE is idempotent - it won't create duplicates, so no WHERE NOT needed
                try:
                    await self.database.execute_query("""
                        MATCH (sd:Scene_Descriptor)
                        MATCH (fp:FusedPlayer)
                        MERGE (sd)-[:HAS_PLAYER]->(fp)
                    """)
                except Exception as e:
                    logger.debug(f"Could not create HAS_PLAYER relationships (Scene_Descriptor may not exist yet): {e}")
                
                logger.debug(f"Updated {len(rows)} FusedPlayer nodes with latest state")
            
            elif batch_type == "Intent":
                # Create/Update Intent nodes (one per camera, persistent, MERGE pattern)
                # Links to CameraConfig node (persistent node, no TTL)
                await self.database.execute_query("""
                    UNWIND $rows AS row
                    // MERGE Intent node by cameraID (only one intent per camera)
                    MERGE (i:Intent {cameraID: row.cameraID})
                    SET i.status = row.status,
                        i.intent_id = row.intent_id,
                        i.intent_type = row.intent_type,
                        i.resolved_ttl_ms = row.resolved_ttl_ms,
                        i.payload = row.payload,
                        i.rule_definition = row.rule_definition,
                        i.reason = row.reason,
                        i.timestamp = row.timestamp
                    
                    // Link to CameraConfig node (persistent node, no TTL)
                    WITH i, row
                    MERGE (cc:CameraConfig {cameraID: row.cameraID})
                    MERGE (cc)-[:HAS_INTENT]->(i)
                """, {"rows": rows})
                
                logger.debug(f"Updated {len(rows)} Intent nodes with latest state")


    async def execute_batch_queries(self, batch_groups: Dict[str, list]) -> None:
        """Alias for execute_queries to maintain test compatibility"""
        return await self.execute_queries(batch_groups) 