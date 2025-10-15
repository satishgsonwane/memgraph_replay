"""
Configuration for NATS Replay Utility
"""

import os
from pathlib import Path
from typing import Optional

class ReplayConfig:
    """Configuration for NATS replay utility"""
    
    def __init__(self):
        # NATS Connection URLs
        self.nats_url = "nats://localhost:4222"
        self.local_nats_url = "nats://localhost:4222"  # Same as nats_url for localhost setup
        
        # Capture settings
        self.default_capture_duration = 30  # seconds
        self.captured_data_dir = Path("data/captured")
        
        # Replay settings
        self.default_framerate = 60.0  # Hz
        self.bridge_startup_delay = 0.5  # seconds - reduced from 2.0s for faster startup
        self.loop_iteration_delay = 0.1  # seconds - delay between loop iterations
        
        # Topic-specific replay rates (Hz) - based on actual captured data analysis
        self.topic_rates = {
            "tickperframe": 25.0,      # ~1440 messages in 60s
            "fused_players": 21.0,     # ~1250 messages in 60s  
            "fusion.ball_3d": 19.0,    # ~1162 messages in 60s
            "ptzinfo.*": 24.0,         # ~1440 messages per camera in 60s
            "all_tracks.*": 12.0,      # Average rate across cameras (~10-14 Hz)
            "intent.*": 1.0,           # Low frequency intent messages
        }
        
        # Default rate for unknown topics
        self.default_topic_rate = 25.0
        
        # Topics to capture
        self.capture_topics = [
            "all_tracks.*",
            "fused_players", 
            "fusion.ball_3d",
            "intent.*",
            "tickperframe",
            "ptzinfo.*"
        ]
        
        # Ensure captured data directory exists
        self.captured_data_dir.mkdir(exist_ok=True)
    
    def get_capture_filename(self, timestamp: str) -> Path:
        """Generate capture filename with timestamp"""
        return self.captured_data_dir / f"capture_{timestamp}.json"
    
    def validate_input_file(self, file_path: str) -> Path:
        """Validate and return Path object for input file"""
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"Input file not found: {file_path}")
        if not path.suffix == '.json':
            raise ValueError(f"Input file must be JSON: {file_path}")
        return path
