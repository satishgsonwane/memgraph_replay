# ---------------------------------------------------
# Configuration file for OZ Game State Bridge
# ---------------------------------------------------
"""
OZ Game State Bridge Configuration

This file contains all configuration parameters for the OZ Game State Bridge service.
The configuration is organized into several categories:

1. Connection Configuration - NATS and Memgraph connection settings
2. Connection Pooling - Database connection pool optimization
3. Time-Based TTL - Data retention and cleanup settings
4. Batch Processing - Message processing optimization
5. Data Structure Defaults - Schema defaults for different data types
6. Topic Filtering - Low-value topic filtering

Performance First Principle: All settings are optimized for high-throughput,
low-latency message processing with sub-10ms P95 latency targets.
"""

import logging
from typing import Optional, Union

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("oz-game-state")

# ===================================================
# CONNECTION CONFIGURATION
# ===================================================

# NATS Message Bus Configuration
# URL for connecting to the NATS message bus server
# Format: nats://host:port
NATS_URL = "nats://localhost:4222"

# Memgraph Database Configuration
# Host and port for the Memgraph graph database
MEMGRAPH_HOST = "localhost"  # Database host address
MEMGRAPH_PORT = 7687         # Default Bolt protocol port for Memgraph

# Service Host Configuration
# Local host address for the service
HOST = "127.0.0.1"

# ===================================================
# CONNECTION POOLING CONFIGURATION
# ===================================================
"""
Connection pooling settings optimized for high-throughput message processing.
These settings balance performance with resource usage.
"""

# Number of database connections to maintain in the pool
# Increased from 5 to 15 for better throughput under high load
CONNECTION_POOL_SIZE = 15

# Timeout for establishing database connections (milliseconds)
# Reduced from default to detect connection failures faster
CONNECTION_TIMEOUT_MS = 100

# Maximum time allowed for individual database queries (milliseconds)
# Prevents blocking operations that could impact message processing
QUERY_TIMEOUT_MS = 50

# ===================================================
# TIME-BASED TTL CONFIGURATION (PRIMARY)
# ===================================================
"""
Time-based Time To Live (TTL) system for data retention and cleanup.
This is the primary TTL system, replacing the legacy tick-based approach.
"""

# Data retention period in seconds
# Set to 30 seconds for extended data retention
ROLLING_WINDOW_SECONDS = 30

# How often to run cleanup operations (seconds)
# Very frequent cleanup to prevent database bloat
CLEANUP_INTERVAL_SECONDS = 1

# Maximum time allowed for cleanup operations (milliseconds)
# Prevents cleanup from blocking message processing
MAX_CLEANUP_TIME_MS = 50

# ===================================================
# LEGACY TICK-BASED CONFIGURATION (DEPRECATED)
# ===================================================
"""
Legacy tick-based TTL configuration kept for backward compatibility.
These parameters are deprecated and should not be used in new code.
Use the time-based TTL configuration above instead.
"""

# Deprecated: Use ROLLING_WINDOW_SECONDS instead
ROLLING_WINDOW = 500

# Deprecated: Use CLEANUP_INTERVAL_SECONDS instead
CLEANUP_INTERVAL = 100

# ===================================================
# BATCH PROCESSING CONFIGURATION
# ===================================================
"""
Ultra-low latency batch processing settings optimized for sub-10ms P95 latency.
These settings balance throughput with processing speed.
"""

# Time interval between batch processing (seconds)
# Ultra-low latency: 2ms interval for sub-10ms P95 latency
BATCH_INTERVAL = 0.005 # 4ms for sub-10ms P95

# Maximum number of messages per batch
# Reduced for faster processing per batch
MAX_BATCH_SIZE = 200

# Minimal delay before cleanup operations (seconds)
# Ensures cleanup doesn't interfere with message processing
CLEANUP_BASE_DELAY = 0.01

# ===================================================
# DATA STRUCTURE DEFAULTS
# ===================================================
"""
Default values for different data types to ensure consistent structure.
These defaults match the schema definitions and handle field variations.
"""

# Player Detection Defaults
# Based on DetectionModel schema - contains all possible player detection fields
PLAYER_DEFAULTS = {
    "category": None,  # ObjectCategory enum: 'player' or 'referee'
    "track_id": None,  # Unique identifier for the player track
    "bbox": None,      # Bounding box coordinates [x1, y1, x2, y2]
    "confidence": None,  # Detection confidence score (0.0-1.0)
    "world_x": None,   # World space X coordinate
    "world_y": None,   # World space Y coordinate
    "transform_PAN": None,   # Camera pan transform
    "transform_TILT": None,  # Camera tilt transform
    "dist": None,      # Distance from camera
    # "keypoints": None, # Keypoint detection data (Dict[str, Any])
    # "attributes": None, # Additional player attributes (Dict[str, Any])
    
    # 3D ray casting properties for player detection
    "ray_origin": None,        # Ray origin in 3D space [x, y, z]
    "ray_world_space_dir": None, # Ray direction in world space [x, y, z]
    
    # Note: vx, vy are commented out in schema
}

# Ball Detection Defaults
# Based on BallTrackModel schema - SEPARATE from player defaults
# Handles both 'confidence' and 'conf' field variations
BALL_DEFAULTS = {
    "world_x": None,   # World space X coordinate
    "world_y": None,   # World space Y coordinate
    "bbox": None,      # Bounding box coordinates [x1, y1, x2, y2]
    "transform_PAN": None,   # Camera pan transform
    "transform_TILT": None,  # Camera tilt transform
    "confidence": None, # Detection confidence (alternative field name)
    "dist": None,      # Distance from camera
    "phi": None,       # Angular position
    "track_id": None,  # Unique identifier for the ball track
    "velocity": None,  # Ball velocity vector
    "movement_score": None,    # Movement quality score
    "velocity_direction": None, # Velocity direction vector
    "velocity_x": None,        # X component of velocity
    "velocity_y": None,        # Y component of velocity
    "is_best": None,   # Whether this is the best ball detection
    "id_score": None,  # Identity score (only present in best_track)
    "dist_score": None, # Distance score (only present in best_track)
    
    # 3D ray casting properties for ball detection
    "ray_origin": None,        # Ray origin in 3D space [x, y, z]
    "ray_world_space_dir": None, # Ray direction in world space [x, y, z]
}

# PTZ (Pan-Tilt-Zoom) Camera Control Defaults
# Camera control parameters for pan, tilt, and zoom operations
PTZ_DEFAULTS = {
    # Current positions
    "panposition": 0.0,    # Current pan position
    "tiltposition": 0.0,   # Current tilt position
    "rollposition": 0.0,   # Current roll position
    "zoomposition": 0.0,   # Current zoom position
    "focusposition": 0.0,  # Current focus position
    
    # Setpoints (target positions)
    "pansetpoint": 0.0,    # Target pan position
    "tiltsetpoint": 0.0,   # Target tilt position
    "zoomsetpoint": 0.0,   # Target zoom position
    
    # Power settings
    "panpower": 0.0,       # Pan motor power
    "tiltpower": 0.0,      # Tilt motor power
    "rollpower": 0.0,      # Roll motor power
    
    # Speed settings
    "pan": 0.0,            # Pan speed
    "tilt": 0.0,           # Tilt speed
    "zoomspeed": 0.0,      # Zoom speed
    
    # System properties
    "tickID": None,        # Associated tick identifier
    
    # Velocity properties (from updated all_tracks message structure)
    "panvelocity": 0.0,    # Pan velocity
    "tiltvelocity": 0.0,   # Tilt velocity
    "zoomvelocity": 0.0,   # Zoom velocity
}

# Camera Parameters Defaults
# Camera intrinsic and extrinsic parameters for 3D reconstruction
CAM_PARAMS_DEFAULTS = {
    # Intrinsic camera matrix (3x3)
    "intrinsic": None,     # Camera intrinsic matrix [[fx, 0, cx], [0, fy, cy], [0, 0, 1]]
    
    # Camera rotation matrix (3x3)
    "rotation": None,      # Camera rotation matrix for world space transformation
    
    # Camera translation vector (3x1)
    "translation": None,   # Camera translation vector [x, y, z] in world space
    
    # System properties
    "tickID": None,        # Associated tick identifier
}

# Fusion Ball 3D Defaults
# Based on FusionBall3DModel schema - SEPARATE from player defaults
FUSION_BALL_3D_DEFAULTS = {
    "timestamp": None,    # Timestamp of the fusion
    "position_world": None,   # World space position of the fusion (stored as 3dposition in node)
    "velocity_mps": None, # Velocity of the fusion in m/s
    "status": None, # Status of the fusion
    "fusion_method": None, # Method used to fuse the data
    "kalman_filtered": None, # Kalman filtered data
    "smooth_2d": None, # Smooth 2D data
    "camera_ready": None, # Camera ready data
}

# ===================================================
# USD SCENE DESCRIPTOR DEFAULTS
# ===================================================
"""
USD-based Scene Descriptor schema for persistent game state representation.
These nodes persist indefinitely with no TTL (current game state).
"""

# Scene Descriptor Defaults
# Singleton node representing venue-level invariants
SCENE_DESCRIPTOR_DEFAULTS = {
    "venue_id": None,       # Venue identifier
    "units": "meters",      # Measurement units
    "up_axis": "Z",         # Vertical axis convention
    "origin": "PITCH_TOP_LEFT",  # Coordinate system origin
    "handedness": "RIGHT",  # Coordinate system handedness
    "version": "1.0",       # Schema version
    "pitch_markers": None,  # Dict of pitch landmark coordinates
}

# Fused Player Defaults
# Real-time player state from fusion algorithm (25 players)
FUSED_PLAYER_DEFAULTS = {
    "id": None,         # Player unique identifier (1-25)
    "x": None,          # World X coordinate in meters
    "y": None,          # World Y coordinate in meters
    "z": 0.0,           # World Z coordinate (typically 0 for ground)
    "vel_x": None,      # Velocity X component in m/s
    "vel_y": None,      # Velocity Y component in m/s
    "status": None,     # Tracking status ('tracked' or 'predicted')
    "category": None,   # Player category ('player' or 'referee')
    "team": None,       # Team assignment ('team_A', 'team_B', or 'none')
}

# Camera Config Defaults
# Static camera configuration data (6 cameras)
CAMERA_CONFIG_DEFAULTS = {
    "cameraID": None,           # Camera identifier (camera1-6)
    "role": None,               # Camera role (main, center, l_sideline, r_sideline, l_goal, r_goal)
    "status": "ACTIVE",         # Camera status
    "operation_mode": None,     # Operation mode (manual, auto)
    "zoom_mode": None,          # Zoom mode (wide, closeup)
    "pan_range": None,          # Pan range limits [min, max]
    "tilt_range": None,         # Tilt range limits [min, max]
    "zoom_range": None,         # Zoom range limits [min, max]
    "camerapos": None,          # Camera position [x, y, z]
    "venue": None,              # Venue identifier
    "gimbal_position": None,    # Current gimbal position {pan, tilt, zoom} - updated from all_tracks
    "camera_parameters": None,  # Camera parameters {intrinsic, rotation, translation} - updated from all_tracks
}

# Intent Defaults
# Based on intents.processed NATS topic schema
# Persistent storage (no TTL cleanup, one intent per camera)
INTENT_DEFAULTS = {
    "status": None,           # "active" or "expired"
    "intent_id": None,        # UUID or "superseded"
    "camera_id": None,        # Camera identifier (e.g., "camera5")
    "intent_type": None,      # Intent type (e.g., "nudge_tilt", "nudge_pan", "none", "unknown")
    "resolved_ttl_ms": None,  # Resolved TTL in milliseconds
    "payload": None,          # Intent payload (dict or null)
    "rule_definition": None,  # Rule definition (dict or null)
    "reason": None,           # Reason for status (e.g., "SUPERSEDED", "TTL_EXPIRED", null)
}

# ===================================================
# TOPIC FILTERING CONFIGURATION
# ===================================================
"""
Low-value topics that should be filtered out to reduce processing load.
These topics provide minimal value for game state analysis.
"""

# Topics to filter out as they provide low-value data
# Reduces processing load and focuses on high-value game state data
LOW_VALUE_TOPICS = [
    "fps.",              # Frames per second data
    "colour-control.",   # Color control settings
    "camera_mode_entry." # Camera mode entry events
]

# ===================================================
# CONFIGURATION CLASS
# ===================================================

class BridgeConfig:
    """
    Configuration object for dependency injection with time-based TTL support.
    
    This class provides a centralized way to manage all configuration parameters
    with proper encapsulation and validation. It supports both time-based TTL
    (primary) and legacy tick-based TTL (deprecated) for backward compatibility.
    
    Usage:
        config = BridgeConfig()  # Use defaults
        config = BridgeConfig(rolling_window_seconds=60)  # Override specific values
    """
    
    def __init__(self, 
                 # Connection Configuration
                 nats_url: str = NATS_URL,
                 memgraph_host: str = MEMGRAPH_HOST,
                 memgraph_port: int = MEMGRAPH_PORT,
                 
                 # Time-based TTL configuration (primary)
                 rolling_window_seconds: int = ROLLING_WINDOW_SECONDS,
                 cleanup_interval_seconds: int = CLEANUP_INTERVAL_SECONDS,
                 max_cleanup_time_ms: int = MAX_CLEANUP_TIME_MS,
                 
                 # Legacy tick-based configuration (deprecated)
                 rolling_window: int = ROLLING_WINDOW,
                 cleanup_interval: int = CLEANUP_INTERVAL,
                 
                 # Batch processing configuration
                 batch_interval: float = BATCH_INTERVAL,
                 max_batch_size: int = MAX_BATCH_SIZE,
                 cleanup_base_delay: float = CLEANUP_BASE_DELAY,
                 
                 # Connection pooling configuration
                 connection_pool_size: int = CONNECTION_POOL_SIZE,
                 connection_timeout_ms: int = CONNECTION_TIMEOUT_MS,
                 query_timeout_ms: int = QUERY_TIMEOUT_MS):
        """
        Initialize BridgeConfig with specified parameters.
        
        Args:
            nats_url: NATS message bus URL
            memgraph_host: Memgraph database host
            memgraph_port: Memgraph database port
            rolling_window_seconds: Data retention period in seconds
            cleanup_interval_seconds: Cleanup frequency in seconds
            max_cleanup_time_ms: Maximum cleanup time in milliseconds
            rolling_window: Legacy tick-based window (deprecated)
            cleanup_interval: Legacy tick-based cleanup (deprecated)
            batch_interval: Batch processing interval in seconds
            max_batch_size: Maximum messages per batch
            cleanup_base_delay: Cleanup delay in seconds
            connection_pool_size: Database connection pool size
            connection_timeout_ms: Connection timeout in milliseconds
            query_timeout_ms: Query timeout in milliseconds
        """
        # Connection configuration
        self.nats_url = nats_url
        self.memgraph_host = memgraph_host
        self.memgraph_port = memgraph_port
        
        # Time-based TTL configuration (primary)
        self._rolling_window_seconds = rolling_window_seconds
        self._cleanup_interval_seconds = cleanup_interval_seconds
        self._max_cleanup_time_ms = max_cleanup_time_ms
        
        # Legacy tick-based configuration (deprecated)
        self._rolling_window = rolling_window
        self._cleanup_interval = cleanup_interval
        
        # Batch processing configuration
        self._batch_interval = batch_interval
        self._max_batch_size = max_batch_size
        self._cleanup_base_delay = cleanup_base_delay
        
        # Connection pooling configuration
        self._connection_pool_size = connection_pool_size
        self._connection_timeout_ms = connection_timeout_ms
        self._query_timeout_ms = query_timeout_ms

    # ===================================================
    # TIME-BASED TTL PROPERTIES (PRIMARY)
    # ===================================================
    
    @property
    def rolling_window_seconds(self) -> int:
        """
        Getter for rolling_window_seconds.
        
        Returns:
            Data retention period in seconds
        """
        return self._rolling_window_seconds

    @property
    def cleanup_interval_seconds(self) -> int:
        """
        Getter for cleanup_interval_seconds.
        
        Returns:
            Cleanup frequency in seconds
        """
        return self._cleanup_interval_seconds

    @property
    def max_cleanup_time_ms(self) -> int:
        """
        Getter for max_cleanup_time_ms.
        
        Returns:
            Maximum cleanup time in milliseconds
        """
        return self._max_cleanup_time_ms

    # ===================================================
    # LEGACY TICK-BASED PROPERTIES (DEPRECATED)
    # ===================================================
    
    @property
    def rolling_window(self) -> int:
        """
        Getter for rolling_window (deprecated: use rolling_window_seconds).
        
        Returns:
            Legacy tick-based window size
        """
        return self._rolling_window

    @property
    def cleanup_interval(self) -> int:
        """
        Getter for cleanup_interval (deprecated: use cleanup_interval_seconds).
        
        Returns:
            Legacy tick-based cleanup interval
        """
        return self._cleanup_interval

    # ===================================================
    # BATCH PROCESSING PROPERTIES
    # ===================================================
    
    @property
    def batch_interval(self) -> float:
        """
        Getter for batch_interval.
        
        Returns:
            Batch processing interval in seconds
        """
        return self._batch_interval

    @property
    def max_batch_size(self) -> int:
        """
        Getter for max_batch_size.
        
        Returns:
            Maximum number of messages per batch
        """
        return self._max_batch_size

    @property
    def cleanup_base_delay(self) -> float:
        """
        Getter for cleanup_base_delay.
        
        Returns:
            Cleanup delay in seconds
        """
        return self._cleanup_base_delay

    # ===================================================
    # CONNECTION POOLING PROPERTIES
    # ===================================================
    
    @property
    def connection_pool_size(self) -> int:
        """
        Getter for connection_pool_size.
        
        Returns:
            Database connection pool size
        """
        return self._connection_pool_size

    @property
    def connection_timeout_ms(self) -> int:
        """
        Getter for connection_timeout_ms.
        
        Returns:
            Connection timeout in milliseconds
        """
        return self._connection_timeout_ms

    @property
    def query_timeout_ms(self) -> int:
        """
        Getter for query_timeout_ms.
        
        Returns:
            Query timeout in milliseconds
        """
        return self._query_timeout_ms

    # ===================================================
    # UTILITY METHODS
    # ===================================================
    
    def __repr__(self) -> str:
        """
        String representation of the configuration.
        
        Returns:
            Formatted string representation
        """
        return (f"BridgeConfig(nats_url={self.nats_url}, "
                f"memgraph_host={self.memgraph_host}, "
                f"memgraph_port={self.memgraph_port}, "
                f"rolling_window_seconds={self.rolling_window_seconds}, "
                f"cleanup_interval_seconds={self.cleanup_interval_seconds}, "
                f"max_cleanup_time_ms={self.max_cleanup_time_ms}, "
                f"batch_interval={self.batch_interval}, "
                f"max_batch_size={self.max_batch_size}, "
                f"cleanup_base_delay={self.cleanup_base_delay}, "
                f"connection_pool_size={self.connection_pool_size}, "
                f"connection_timeout_ms={self.connection_timeout_ms}, "
                f"query_timeout_ms={self.query_timeout_ms})")

    def to_dict(self) -> dict:
        """
        Convert configuration to dictionary.
        
        Returns:
            Dictionary representation of all configuration parameters
        """
        return {
            # Connection configuration
            'nats_url': self.nats_url,
            'memgraph_host': self.memgraph_host,
            'memgraph_port': self.memgraph_port,
            
            # Time-based TTL configuration (primary)
            'rolling_window_seconds': self.rolling_window_seconds,
            'cleanup_interval_seconds': self.cleanup_interval_seconds,
            'max_cleanup_time_ms': self.max_cleanup_time_ms,
            
            # Batch processing configuration
            'batch_interval': self.batch_interval,
            'max_batch_size': self.max_batch_size,
            'cleanup_base_delay': self.cleanup_base_delay,
            
            # Connection pooling configuration
            'connection_pool_size': self.connection_pool_size,
            'connection_timeout_ms': self.connection_timeout_ms,
            'query_timeout_ms': self.query_timeout_ms,
            
            # Legacy properties for backward compatibility
            'rolling_window': self.rolling_window,
            'cleanup_interval': self.cleanup_interval
        } 