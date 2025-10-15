#!/usr/bin/env python3
"""
Example usage of NATS Replay Utility

This script demonstrates how to use the replay utility programmatically.
"""

import asyncio
import logging
from pathlib import Path

from replay_utility.capture import NATSCapture
from replay_utility.replay import NATSReplay
from replay_utility.config import ReplayConfig

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def example_capture():
    """Example: Capture messages for 10 seconds"""
    logger.info("=== Example: Capturing Messages ===")
    
    config = ReplayConfig()
    capture = NATSCapture(config)
    
    try:
        # Capture for 10 seconds
        saved_path = await capture.run_capture(duration=10.0)
        logger.info(f"Messages captured to: {saved_path}")
        return saved_path
    except Exception as e:
        logger.error(f"Capture failed: {e}")
        return None

async def example_replay(file_path: Path):
    """Example: Replay captured messages"""
    logger.info("=== Example: Replaying Messages ===")
    
    config = ReplayConfig()
    replay = NATSReplay(config)
    
    try:
        await replay.run_replay(file_path)
        logger.info("Replay completed successfully")
    except Exception as e:
        logger.error(f"Replay failed: {e}")

async def example_custom_config():
    """Example: Using custom configuration"""
    logger.info("=== Example: Custom Configuration ===")
    
    # Create custom config
    config = ReplayConfig()
    config.default_capture_duration = 5.0  # 5 seconds
    config.default_framerate = 30.0  # 30 Hz
    
    logger.info(f"Custom capture duration: {config.default_capture_duration}s")
    logger.info(f"Custom framerate: {config.default_framerate} Hz")
    
    # Use custom config for capture
    capture = NATSCapture(config)
    
    try:
        saved_path = await capture.run_capture()
        logger.info(f"Custom capture completed: {saved_path}")
        return saved_path
    except Exception as e:
        logger.error(f"Custom capture failed: {e}")
        return None

async def main():
    """Run all examples"""
    logger.info("NATS Replay Utility Examples")
    logger.info("=" * 50)
    
    # Example 1: Basic capture
    captured_file = await example_capture()
    
    if captured_file:
        # Example 2: Basic replay
        await example_replay(captured_file)
    
    # Example 3: Custom configuration
    await example_custom_config()
    
    logger.info("=" * 50)
    logger.info("Examples completed!")

if __name__ == "__main__":
    asyncio.run(main())
