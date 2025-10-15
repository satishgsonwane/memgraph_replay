"""
Query utilities for track-based schema operations.
Provides functions to query recent tracks and track history.
"""

from typing import List, Dict, Any, Optional
from src.core.interfaces import DatabaseInterface

class TrackQueryUtils:
    """Utility class for querying track-based data"""
    
    def __init__(self, database: DatabaseInterface):
        self.database = database
    
    async def get_recent_player_tracks(self) -> List[Dict[str, Any]]:
        """Get the most recent detection from each player track"""
        query = """
        MATCH (pt:PlayerTrack)
        WHERE size(pt.timestamps) > 0
        RETURN 
            pt.track_id as track_id,
            pt.cameraID as cameraID,
            pt.category as category,
            pt.world_x[-1] as latest_world_x,
            pt.world_y[-1] as latest_world_y,
            pt.confidence[-1] as latest_confidence,
            pt.timestamps[-1] as latest_timestamp,
            pt.tickIDs[-1] as latest_tickID,
            size(pt.timestamps) as detection_count
        ORDER BY pt.last_updated DESC
        """
        result = await self.database.execute_query(query)
        # Convert tuples to dictionaries
        return [
            {
                'track_id': row[0],
                'cameraID': row[1],
                'category': row[2],
                'latest_world_x': row[3],
                'latest_world_y': row[4],
                'latest_confidence': row[5],
                'latest_timestamp': row[6],
                'latest_tickID': row[7],
                'detection_count': row[8]
            }
            for row in result
        ]
    
    async def get_recent_ball_tracks(self) -> List[Dict[str, Any]]:
        """Get the most recent detection from each ball track"""
        query = """
        MATCH (bt:BallTrack)
        WHERE size(bt.timestamps) > 0
        RETURN 
            bt.track_id as track_id,
            bt.cameraID as cameraID,
            bt.world_x[-1] as latest_world_x,
            bt.world_y[-1] as latest_world_y,
            bt.conf[-1] as latest_confidence,
            bt.timestamps[-1] as latest_timestamp,
            bt.tickIDs[-1] as latest_tickID,
            size(bt.timestamps) as detection_count
        ORDER BY bt.last_updated DESC
        """
        result = await self.database.execute_query(query)
        # Convert tuples to dictionaries
        return [
            {
                'track_id': row[0],
                'cameraID': row[1],
                'latest_world_x': row[2],
                'latest_world_y': row[3],
                'latest_confidence': row[4],
                'latest_timestamp': row[5],
                'latest_tickID': row[6],
                'detection_count': row[7]
            }
            for row in result
        ]
    
    async def get_recent_n_detections_player(self, track_id: int, cameraID: str, n: int = 10) -> Dict[str, Any]:
        """Get the recent n detections from a specific player track"""
        query = """
        MATCH (pt:PlayerTrack {track_id: $track_id, cameraID: $cameraID})
        WHERE size(pt.timestamps) > 0
        WITH pt, CASE WHEN size(pt.timestamps) < $n THEN 0 ELSE size(pt.timestamps) - $n END as start_idx
        RETURN 
            pt.track_id as track_id,
            pt.cameraID as cameraID,
            pt.category as category,
            pt.world_x[start_idx..] as world_x_history,
            pt.world_y[start_idx..] as world_y_history,
            pt.confidence[start_idx..] as confidence_history,
            pt.timestamps[start_idx..] as timestamp_history,
            pt.tickIDs[start_idx..] as tickID_history,
            size(pt.timestamps) as total_detections
        """
        result = await self.database.execute_query(query, {
            "track_id": track_id, 
            "cameraID": cameraID, 
            "n": n
        })
        if result:
            row = result[0]
            return {
                'track_id': row[0],
                'cameraID': row[1],
                'category': row[2],
                'world_x_history': row[3],
                'world_y_history': row[4],
                'confidence_history': row[5],
                'timestamp_history': row[6],
                'tickID_history': row[7],
                'total_detections': row[8]
            }
        return None
    
    async def get_recent_n_detections_ball(self, track_id: int, cameraID: str, n: int = 10) -> Dict[str, Any]:
        """Get the recent n detections from a specific ball track"""
        query = """
        MATCH (bt:BallTrack {track_id: $track_id, cameraID: $cameraID})
        WHERE size(bt.timestamps) > 0
        WITH bt, CASE WHEN size(bt.timestamps) < $n THEN 0 ELSE size(bt.timestamps) - $n END as start_idx
        RETURN 
            bt.track_id as track_id,
            bt.cameraID as cameraID,
            bt.world_x[start_idx..] as world_x_history,
            bt.world_y[start_idx..] as world_y_history,
            bt.conf[start_idx..] as confidence_history,
            bt.timestamps[start_idx..] as timestamp_history,
            bt.tickIDs[start_idx..] as tickID_history,
            size(bt.timestamps) as total_detections
        """
        result = await self.database.execute_query(query, {
            "track_id": track_id, 
            "cameraID": cameraID, 
            "n": n
        })
        if result:
            row = result[0]
            return {
                'track_id': row[0],
                'cameraID': row[1],
                'world_x_history': row[2],
                'world_y_history': row[3],
                'confidence_history': row[4],
                'timestamp_history': row[5],
                'tickID_history': row[6],
                'total_detections': row[7]
            }
        return None
    
    async def get_all_active_tracks_at_tick(self, tickID: int) -> Dict[str, List[Dict[str, Any]]]:
        """Get all tracks that were active at a specific tick"""
        query = """
        MATCH (f:Frame {tickID: $tickID})-[:HAS_ACTIVE_TRACK]->(track)
        WHERE track:PlayerTrack OR track:BallTrack
        WITH track, labels(track)[0] as track_type
        OPTIONAL MATCH (track)-[:TRACKS_PLAYER|TRACKS_BALL]-(c:Camera)
        WITH track, track_type, c.cameraID as cameraID
        WHERE $tickID IN track.tickIDs
        WITH track, track_type, cameraID, 
             [i IN range(0, size(track.tickIDs)-1) WHERE track.tickIDs[i] = $tickID][0] as tick_index
        RETURN 
            track_type,
            track.track_id as track_id,
            cameraID,
            CASE WHEN track_type = 'PlayerTrack' THEN track.category ELSE null END as category,
            track.world_x[tick_index] as world_x,
            track.world_y[tick_index] as world_y,
            CASE 
                WHEN track_type = 'PlayerTrack' THEN track.confidence[tick_index] 
                ELSE track.conf[tick_index] 
            END as confidence,
            track.timestamps[tick_index] as timestamp
        """
        result = await self.database.execute_query(query, {"tickID": tickID})
        
        # Group by track type
        grouped = {"players": [], "balls": []}
        for row in result:
            track_type = row[0]
            track_data = {
                "track_id": row[1],
                "cameraID": row[2],
                "world_x": row[4],
                "world_y": row[5],
                "confidence": row[6],
                "timestamp": row[7]
            }
            if track_type == "PlayerTrack":
                track_data["category"] = row[3]
                grouped["players"].append(track_data)
            else:
                grouped["balls"].append(track_data)
        
        return grouped
    
    async def get_track_statistics(self) -> Dict[str, Any]:
        """Get statistics about track data"""
        query = """
        MATCH (pt:PlayerTrack)
        WITH count(pt) as player_track_count, 
             sum([track IN collect(pt) | size(track.timestamps)]) as total_player_detections
        MATCH (bt:BallTrack)
        WITH player_track_count, total_player_detections,
             count(bt) as ball_track_count,
             sum([track IN collect(bt) | size(track.timestamps)]) as total_ball_detections
        RETURN 
            player_track_count,
            ball_track_count,
            CASE WHEN player_track_count > 0 THEN toFloat(total_player_detections) / player_track_count ELSE 0 END as avg_player_detections,
            CASE WHEN ball_track_count > 0 THEN toFloat(total_ball_detections) / ball_track_count ELSE 0 END as avg_ball_detections
        """
        result = await self.database.execute_query(query)
        if result:
            return {
                "player_track_count": result[0][0],
                "ball_track_count": result[0][1], 
                "avg_player_detections": result[0][2],
                "avg_ball_detections": result[0][3]
            }
        return {"player_track_count": 0, "ball_track_count": 0, "avg_player_detections": 0, "avg_ball_detections": 0}
    
    async def find_closest_player_to_ball(self, ball_track_id: int, ball_cameraID: str) -> Optional[Dict[str, Any]]:
        """Find the player track closest to a specific ball track (using latest positions)"""
        query = """
        MATCH (bt:BallTrack {track_id: $ball_track_id, cameraID: $ball_cameraID})
        WHERE size(bt.world_x) > 0 AND size(bt.world_y) > 0
        WITH bt.world_x[-1] as ball_x, bt.world_y[-1] as ball_y, bt.timestamps[-1] as ball_time
        
        MATCH (pt:PlayerTrack)
        WHERE size(pt.world_x) > 0 AND size(pt.world_y) > 0
        WITH ball_x, ball_y, ball_time, pt,
             pt.world_x[-1] as player_x, pt.world_y[-1] as player_y,
             sqrt((pt.world_x[-1] - ball_x)^2 + (pt.world_y[-1] - ball_y)^2) as distance
        ORDER BY distance ASC
        LIMIT 1
        RETURN 
            pt.track_id as player_track_id,
            pt.cameraID as player_cameraID,
            pt.category as category,
            player_x,
            player_y,
            pt.timestamps[-1] as player_time,
            distance
        """
        result = await self.database.execute_query(query, {
            "ball_track_id": ball_track_id,
            "ball_cameraID": ball_cameraID
        })
        if result:
            row = result[0]
            return {
                "player_track_id": row[0],
                "player_cameraID": row[1],
                "category": row[2],
                "world_x": row[3],
                "world_y": row[4],
                "timestamp": row[5],
                "distance": row[6]
            }
        return None
