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
        self.bridge_startup_delay = 2.0  # seconds
        
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
