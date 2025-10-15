"""
NATS Replay Utility Package

A self-contained utility for capturing NATS messages to JSON and replaying them
at ticker speed with Memgraph bridge integration.

Usage:
    python -m replay_utility capture --duration 30
    python -m replay_utility replay --input captured_data/capture_20250127_120000.json
"""

__version__ = "1.0.0"
__author__ = "OZ Engineering"

from .capture import NATSCapture
from .replay import NATSReplay
from .runner import main
from .config import ReplayConfig

__all__ = ["NATSCapture", "NATSReplay", "main", "ReplayConfig"]
