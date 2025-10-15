#!/usr/bin/env python3
"""
Query Recent Tracks by Camera

This script queries the Memgraph database to get the most recent tracks from each camera
based on the current timestamp with a 20ms threshold. It handles the one-node-per-detection
architecture where each PlayerTrack and BallTrack node contains arrays of detection data.

Usage:
    python query_recent_tracks_by_camera.py

Requirements:
    - Memgraph database running on localhost:7687
    - mgclient Python library
"""

import asyncio
import mgclient
import time
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

# Configuration
MEMGRAPH_HOST = "localhost"
MEMGRAPH_PORT = 7687
THRESHOLD_MS = 100000  # 20ms threshold as requested


@dataclass
class TrackDetection:
    """Represents a single track detection"""
    track_id: int
    camera_id: str
    track_type: str  # 'player' or 'ball'
    timestamp: str
    world_x: Optional[float]
    world_y: Optional[float]
    confidence: Optional[float]
    category: Optional[str] = None  # Only for player tracks


class RecentTracksQuery:
    """Query utility for getting recent tracks by camera"""
    
    def __init__(self, host: str = MEMGRAPH_HOST, port: int = MEMGRAPH_PORT):
        self.host = host
        self.port = port
        self.connection = None
    
    def connect(self):
        """Connect to Memgraph database"""
        try:
            self.connection = mgclient.connect(host=self.host, port=self.port)
            self.connection.autocommit = True
            print(f"✅ Connected to Memgraph at {self.host}:{self.port}")
        except Exception as e:
            print(f"❌ Failed to connect to Memgraph: {e}")
            raise
    
    def disconnect(self):
        """Disconnect from Memgraph database"""
        if self.connection:
            self.connection.close()
            print("🔌 Disconnected from Memgraph")
    
    def execute_query(self, query: str, parameters: Optional[Dict[str, Any]] = None) -> List[Any]:
        """Execute a query and return results"""
        try:
            cursor = self.connection.cursor()
            cursor.execute(query, parameters or {})
            return cursor.fetchall()
        except Exception as e:
            print(f"❌ Query execution failed: {e}")
            raise
    
    def get_current_timestamp_with_threshold(self) -> str:
        """Get current timestamp minus threshold in ISO format"""
        current_time = datetime.utcnow()
        threshold_time = current_time - timedelta(milliseconds=THRESHOLD_MS)
        return threshold_time.strftime('%Y-%m-%dT%H:%M:%S.%fZ')[:-3] + 'Z'
    
    def get_recent_player_tracks_by_camera(self, threshold_timestamp: str) -> List[TrackDetection]:
        """
        Get recent player tracks from each camera within the threshold.
        
        The PlayerTrack nodes have individual timestamp properties, not arrays.
        """
        query = """
        MATCH (c:Camera)-[:TRACKS_PLAYER]->(pt:PlayerTrack)
        WHERE pt.timestamp >= $threshold_timestamp
        
        RETURN 
            pt.track_id as track_id,
            c.cameraID as camera_id,
            pt.timestamp as timestamp,
            pt.world_x as world_x,
            pt.world_y as world_y,
            pt.confidence as confidence,
            pt.category as category
        ORDER BY camera_id, timestamp DESC
        """
        
        try:
            results = self.execute_query(query, {"threshold_timestamp": threshold_timestamp})
            tracks = []
            
            for row in results:
                track = TrackDetection(
                    track_id=row[0],
                    camera_id=row[1],
                    track_type="player",
                    timestamp=row[2],
                    world_x=row[3],
                    world_y=row[4],
                    confidence=row[5],
                    category=row[6]
                )
                tracks.append(track)
            
            return tracks
            
        except Exception as e:
            print(f"❌ Error querying player tracks: {e}")
            return []
    
    def get_recent_ball_tracks_by_camera(self, threshold_timestamp: str) -> List[TrackDetection]:
        """
        Get recent ball tracks from each camera within the threshold.
        
        The BallTrack nodes have individual timestamp properties, not arrays.
        """
        query = """
        MATCH (c:Camera)-[:TRACKS_BALL]->(bt:BallTrack)
        WHERE bt.timestamp >= $threshold_timestamp
        
        RETURN 
            bt.track_id as track_id,
            c.cameraID as camera_id,
            bt.timestamp as timestamp,
            bt.world_x as world_x,
            bt.world_y as world_y,
            bt.confidence as confidence
        ORDER BY camera_id, timestamp DESC
        """
        
        try:
            results = self.execute_query(query, {"threshold_timestamp": threshold_timestamp})
            tracks = []
            
            for row in results:
                track = TrackDetection(
                    track_id=row[0],
                    camera_id=row[1],
                    track_type="ball",
                    timestamp=row[2],
                    world_x=row[3],
                    world_y=row[4],
                    confidence=row[5]
                )
                tracks.append(track)
            
            return tracks
            
        except Exception as e:
            print(f"❌ Error querying ball tracks: {e}")
            return []
    
    def get_all_recent_tracks_by_camera(self) -> Dict[str, Dict[str, List[TrackDetection]]]:
        """
        Get all recent tracks (players and balls) grouped by camera.
        
        Returns:
            Dict with structure: {
                'camera1': {
                    'players': [TrackDetection, ...],
                    'balls': [TrackDetection, ...]
                },
                ...
            }
        """
        threshold_timestamp = self.get_current_timestamp_with_threshold()
        print(f"🕐 Querying tracks with threshold: {threshold_timestamp} (current time - {THRESHOLD_MS}ms)")
        
        # Get player and ball tracks
        player_tracks = self.get_recent_player_tracks_by_camera(threshold_timestamp)
        ball_tracks = self.get_recent_ball_tracks_by_camera(threshold_timestamp)
        
        # Group by camera
        cameras = {}
        
        # Process player tracks
        for track in player_tracks:
            if track.camera_id not in cameras:
                cameras[track.camera_id] = {'players': [], 'balls': []}
            cameras[track.camera_id]['players'].append(track)
        
        # Process ball tracks
        for track in ball_tracks:
            if track.camera_id not in cameras:
                cameras[track.camera_id] = {'players': [], 'balls': []}
            cameras[track.camera_id]['balls'].append(track)
        
        return cameras
    
    def get_recent_tracks_for_specific_camera(self, camera_id: str) -> Dict[str, List[TrackDetection]]:
        """
        Get recent tracks for a specific camera only.
        
        Args:
            camera_id: The camera ID to query (e.g., 'camera1', 'camera2')
            
        Returns:
            Dict with 'players' and 'balls' lists for the specified camera
        """
        threshold_timestamp = self.get_current_timestamp_with_threshold()
        print(f"🕐 Querying tracks for camera {camera_id} with threshold: {threshold_timestamp}")
        
        # Modified queries to filter by specific camera
        player_query = """
        MATCH (c:Camera {cameraID: $camera_id})-[:TRACKS_PLAYER]->(pt:PlayerTrack)
        WHERE pt.timestamp >= $threshold_timestamp
        
        RETURN 
            pt.track_id as track_id,
            c.cameraID as camera_id,
            pt.timestamp as timestamp,
            pt.world_x as world_x,
            pt.world_y as world_y,
            pt.confidence as confidence,
            pt.category as category
        ORDER BY timestamp DESC
        """
        
        ball_query = """
        MATCH (c:Camera {cameraID: $camera_id})-[:TRACKS_BALL]->(bt:BallTrack)
        WHERE bt.timestamp >= $threshold_timestamp
        
        RETURN 
            bt.track_id as track_id,
            c.cameraID as camera_id,
            bt.timestamp as timestamp,
            bt.world_x as world_x,
            bt.world_y as world_y,
            bt.confidence as confidence
        ORDER BY timestamp DESC
        """
        
        try:
            # Execute queries
            player_results = self.execute_query(player_query, {
                "camera_id": camera_id,
                "threshold_timestamp": threshold_timestamp
            })
            ball_results = self.execute_query(ball_query, {
                "camera_id": camera_id,
                "threshold_timestamp": threshold_timestamp
            })
            
            # Process results
            players = []
            for row in player_results:
                track = TrackDetection(
                    track_id=row[0],
                    camera_id=row[1],
                    track_type="player",
                    timestamp=row[2],
                    world_x=row[3],
                    world_y=row[4],
                    confidence=row[5],
                    category=row[6]
                )
                players.append(track)
            
            balls = []
            for row in ball_results:
                track = TrackDetection(
                    track_id=row[0],
                    camera_id=row[1],
                    track_type="ball",
                    timestamp=row[2],
                    world_x=row[3],
                    world_y=row[4],
                    confidence=row[5]
                )
                balls.append(track)
            
            return {'players': players, 'balls': balls}
            
        except Exception as e:
            print(f"❌ Error querying tracks for camera {camera_id}: {e}")
            return {'players': [], 'balls': []}
    
    def get_tracks_with_custom_threshold(self, threshold_ms: int) -> Dict[str, Dict[str, List[TrackDetection]]]:
        """
        Get recent tracks with a custom threshold (instead of the default 20ms).
        
        Args:
            threshold_ms: Custom threshold in milliseconds
            
        Returns:
            Dict with camera data similar to get_all_recent_tracks_by_camera
        """
        current_time = datetime.utcnow()
        threshold_time = current_time - timedelta(milliseconds=threshold_ms)
        threshold_timestamp = threshold_time.strftime('%Y-%m-%dT%H:%M:%S.%fZ')[:-3] + 'Z'
        
        print(f"🕐 Querying tracks with custom threshold: {threshold_ms}ms ({threshold_timestamp})")
        
        # Get player and ball tracks with custom threshold
        player_tracks = self.get_recent_player_tracks_by_camera(threshold_timestamp)
        ball_tracks = self.get_recent_ball_tracks_by_camera(threshold_timestamp)
        
        # Group by camera
        cameras = {}
        
        for track in player_tracks:
            if track.camera_id not in cameras:
                cameras[track.camera_id] = {'players': [], 'balls': []}
            cameras[track.camera_id]['players'].append(track)
        
        for track in ball_tracks:
            if track.camera_id not in cameras:
                cameras[track.camera_id] = {'players': [], 'balls': []}
            cameras[track.camera_id]['balls'].append(track)
        
        return cameras
    
    def get_track_counts_by_camera(self) -> Dict[str, Dict[str, int]]:
        """
        Get just the counts of recent tracks by camera (faster query for monitoring).
        
        Returns:
            Dict with structure: {'camera1': {'players': 5, 'balls': 2}, ...}
        """
        threshold_timestamp = self.get_current_timestamp_with_threshold()
        
        query = """
        // Count player tracks by camera
        MATCH (c:Camera)
        OPTIONAL MATCH (c)-[:TRACKS_PLAYER]->(pt:PlayerTrack)
        WHERE pt IS NULL OR pt.timestamp >= $threshold_timestamp
        WITH c.cameraID as camera_id, count(pt) as player_count
        
        // Count ball tracks by camera  
        OPTIONAL MATCH (c2:Camera {cameraID: camera_id})-[:TRACKS_BALL]->(bt:BallTrack)
        WHERE bt IS NULL OR bt.timestamp >= $threshold_timestamp
        
        RETURN camera_id, player_count, count(bt) as ball_count
        """
        
        try:
            results = self.execute_query(query, {"threshold_timestamp": threshold_timestamp})
            counts = {}
            
            for row in results:
                camera_id = row[0]
                player_count = row[1]
                ball_count = row[2]
                
                counts[camera_id] = {
                    'players': player_count,
                    'balls': ball_count
                }
            
            return counts
            
        except Exception as e:
            print(f"❌ Error getting track counts: {e}")
            return {}
    
    def print_results(self, results: Dict[str, Dict[str, List[TrackDetection]]]):
        """Print the results in a formatted way"""
        print("\n" + "="*80)
        print(f"RECENT TRACKS BY CAMERA (within {THRESHOLD_MS}ms threshold)")
        print("="*80)
        
        if not results:
            print("❌ No recent tracks found within the threshold")
            return
        
        total_players = 0
        total_balls = 0
        
        for camera_id in sorted(results.keys()):
            camera_data = results[camera_id]
            player_count = len(camera_data['players'])
            ball_count = len(camera_data['balls'])
            
            total_players += player_count
            total_balls += ball_count
            
            print(f"\n📹 CAMERA: {camera_id}")
            print(f"   Players: {player_count}, Balls: {ball_count}")
            print("-" * 60)
            
            # Print player tracks
            if camera_data['players']:
                print("  👥 PLAYER TRACKS:")
                for track in camera_data['players']:
                    print(f"    Track {track.track_id:>6} | {track.category or 'N/A':>10} | "
                          f"Pos: ({track.world_x:>6.1f}, {track.world_y:>6.1f}) | "
                          f"Conf: {track.confidence:>5.3f} | {track.timestamp}")
            
            # Print ball tracks
            if camera_data['balls']:
                print("  ⚽ BALL TRACKS:")
                for track in camera_data['balls']:
                    print(f"    Track {track.track_id:>6} | {'ball':>10} | "
                          f"Pos: ({track.world_x:>6.1f}, {track.world_y:>6.1f}) | "
                          f"Conf: {track.confidence:>5.3f} | {track.timestamp}")
        
        print("\n" + "="*80)
        print(f"SUMMARY: {len(results)} cameras, {total_players} player tracks, {total_balls} ball tracks")
        print("="*80)
    
    def print_counts_only(self, counts: Dict[str, Dict[str, int]]):
        """Print just the track counts (compact format)"""
        print("\n" + "="*50)
        print(f"TRACK COUNTS BY CAMERA (within {THRESHOLD_MS}ms)")
        print("="*50)
        
        if not counts:
            print("❌ No recent tracks found")
            return
        
        total_players = 0
        total_balls = 0
        
        for camera_id in sorted(counts.keys()):
            player_count = counts[camera_id]['players']
            ball_count = counts[camera_id]['balls']
            total_players += player_count
            total_balls += ball_count
            
            print(f"📹 {camera_id:>8}: {player_count:>3} players, {ball_count:>2} balls")
        
        print("-" * 50)
        print(f"TOTAL: {total_players} players, {total_balls} balls across {len(counts)} cameras")
        print("="*50)


def main():
    """Main function to execute the query with command-line argument support"""
    import argparse
    global THRESHOLD_MS
    parser = argparse.ArgumentParser(
        description="Query recent tracks from each camera in the OZ Game State database",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                           # Get all recent tracks (20ms threshold)
  %(prog)s --threshold 50            # Use 50ms threshold instead of 20ms
  %(prog)s --camera camera1          # Get tracks from camera1 only
  %(prog)s --counts-only             # Show only track counts (faster)
  %(prog)s --camera camera2 --threshold 100  # Camera2 with 100ms threshold
        """
    )
    
    parser.add_argument(
        '--threshold', 
        type=int, 
        default=THRESHOLD_MS,
        help=f'Threshold in milliseconds (default: {THRESHOLD_MS}ms)'
    )
    
    parser.add_argument(
        '--camera',
        type=str,
        help='Query specific camera only (e.g., camera1, camera2)'
    )
    
    parser.add_argument(
        '--counts-only',
        action='store_true',
        help='Show only track counts (faster query)'
    )
    
    parser.add_argument(
        '--host',
        type=str,
        default=MEMGRAPH_HOST,
        help=f'Memgraph host (default: {MEMGRAPH_HOST})'
    )
    
    parser.add_argument(
        '--port',
        type=int,
        default=MEMGRAPH_PORT,
        help=f'Memgraph port (default: {MEMGRAPH_PORT})'
    )
    
    args = parser.parse_args()
    
    print("🚀 Starting Recent Tracks Query by Camera")
    print(f"📊 Threshold: {args.threshold}ms from current timestamp")
    if args.camera:
        print(f"📹 Camera filter: {args.camera}")
    if args.counts_only:
        print("📈 Mode: Counts only (fast)")
    
    query_tool = RecentTracksQuery(host=args.host, port=args.port)
    
    try:
        # Connect to database
        query_tool.connect()
        
        # Execute appropriate query based on arguments
        if args.camera:
            # Query specific camera
            if args.threshold != THRESHOLD_MS:
                print(f"⚠️  Custom threshold with specific camera not fully supported. Using default threshold.")
            
            results = query_tool.get_recent_tracks_for_specific_camera(args.camera)
            # Convert to expected format for printing
            camera_results = {args.camera: results}
            query_tool.print_results(camera_results)
            
        elif args.counts_only:
            # Get counts only
            if args.threshold != THRESHOLD_MS:
                # For counts only with custom threshold, we need to modify the global threshold
                
                original_threshold = THRESHOLD_MS
                THRESHOLD_MS = args.threshold
                counts = query_tool.get_track_counts_by_camera()
                THRESHOLD_MS = original_threshold  # Restore original
            else:
                counts = query_tool.get_track_counts_by_camera()
            
            query_tool.print_counts_only(counts)
            
        else:
            # Get all tracks
            if args.threshold != THRESHOLD_MS:
                results = query_tool.get_tracks_with_custom_threshold(args.threshold)
            else:
                results = query_tool.get_all_recent_tracks_by_camera()
            
            query_tool.print_results(results)
        
    except Exception as e:
        print(f"❌ Script failed: {e}")
        return 1
    
    finally:
        query_tool.disconnect()
    
    print("\n✅ Query completed successfully")
    return 0


if __name__ == "__main__":
    exit(main())

