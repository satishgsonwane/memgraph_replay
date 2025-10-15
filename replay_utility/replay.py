"""
NATS Message Replay Module

Loads captured messages from JSON and replays them to local NATS server
at the framerate specified in tickperframe messages.
"""

import asyncio
import json
import logging
import time
from pathlib import Path
from typing import Dict, List, Any, Optional

import nats
import orjson

from .config import ReplayConfig

logger = logging.getLogger(__name__)

class NATSReplay:
    """Replays captured NATS messages to local server"""
    
    def __init__(self, config: ReplayConfig):
        self.config = config
        self.nc: Optional[nats.NATS] = None
        self.messages: List[Dict[str, Any]] = []
        self.framerate: float = config.default_framerate
        self.replay_interval: float = 1.0 / config.default_framerate
        self.start_time: Optional[float] = None
        self.messages_published: int = 0
        self.current_tick: int = 0
        
    def load_capture_file(self, file_path: Path) -> None:
        """Load captured messages from JSON file"""
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
            
            # Extract metadata and messages
            if 'capture_info' in data and 'messages' in data:
                capture_info = data['capture_info']
                self.messages = data['messages']
                
                logger.info(f"Loaded capture file: {file_path}")
                logger.info(f"Capture info:")
                logger.info(f"  Duration: {capture_info.get('duration_seconds', 'unknown')}s")
                logger.info(f"  Total messages: {len(self.messages)}")
                logger.info(f"  Topics: {capture_info.get('topics_captured', [])}")
                logger.info(f"  Message counts: {capture_info.get('message_counts', {})}")
            else:
                # Fallback: assume direct message list
                self.messages = data
                logger.info(f"Loaded {len(self.messages)} messages from: {file_path}")
            
            if not self.messages:
                raise ValueError("No messages found in capture file")
            
            # Extract framerate from first tickperframe message
            self._extract_framerate()
            
        except Exception as e:
            logger.error(f"Failed to load capture file: {e}")
            raise
    
    def _extract_framerate(self) -> None:
        """Extract framerate from tickperframe messages"""
        for message in self.messages:
            if message['topic'] == 'tickperframe':
                payload = message['payload']
                framerate = payload.get('framerate')
                if framerate and framerate > 0:
                    self.framerate = framerate
                    self.replay_interval = 1.0 / framerate
                    logger.info(f"Extracted framerate: {framerate} Hz (interval: {self.replay_interval:.3f}s)")
                    return
        
        logger.warning(f"No framerate found in tickperframe messages, using default: {self.framerate} Hz")
    
    async def connect(self) -> None:
        """Connect to local NATS server"""
        try:
            self.nc = await nats.connect(self.config.local_nats_url)
            logger.info(f"Connected to local NATS server: {self.config.local_nats_url}")
        except Exception as e:
            logger.error(f"Failed to connect to local NATS: {e}")
            raise
    
    async def publish_message(self, message: Dict[str, Any]) -> None:
        """Publish a single message to NATS"""
        if not self.nc:
            raise RuntimeError("Not connected to NATS")
        
        try:
            topic = message['topic']
            payload = message['payload']
            
            # Serialize payload to JSON bytes
            payload_bytes = orjson.dumps(payload)
            
            # Publish message
            await self.nc.publish(topic, payload_bytes)
            
            # Update statistics
            self.messages_published += 1
            
            # Track current tick from tickperframe messages
            if topic == 'tickperframe':
                self.current_tick = payload.get('count', 0)
            
            # Log progress every 50 messages
            if self.messages_published % 50 == 0:
                elapsed = time.time() - self.start_time if self.start_time else 0
                rate = self.messages_published / elapsed if elapsed > 0 else 0
                logger.info(f"Published {self.messages_published}/{len(self.messages)} messages "
                           f"(tick: {self.current_tick}, rate: {rate:.1f} msg/s)")
                
        except Exception as e:
            logger.error(f"Failed to publish message to {message['topic']}: {e}")
            raise
    
    async def replay_messages(self) -> None:
        """Replay all messages at calculated framerate"""
        if not self.messages:
            raise ValueError("No messages to replay")
        
        logger.info(f"Starting replay of {len(self.messages)} messages at {self.framerate} Hz")
        logger.info(f"Replay interval: {self.replay_interval:.3f}s")
        
        self.start_time = time.time()
        
        try:
            for i, message in enumerate(self.messages):
                # Publish message
                await self.publish_message(message)
                
                # Calculate timing for next message
                if i < len(self.messages) - 1:  # Don't sleep after last message
                    # Calculate when next message should be published
                    target_time = self.start_time + (i + 1) * self.replay_interval
                    current_time = time.time()
                    sleep_duration = target_time - current_time
                    
                    # Only sleep if we're ahead of schedule
                    if sleep_duration > 0:
                        await asyncio.sleep(sleep_duration)
                    else:
                        # Log timing drift if significant
                        drift = -sleep_duration
                        if drift > 0.01:  # > 10ms drift
                            logger.warning(f"Timing drift: {drift*1000:.1f}ms behind schedule")
            
            # Final statistics
            total_time = time.time() - self.start_time
            actual_rate = self.messages_published / total_time
            
            logger.info(f"Replay completed:")
            logger.info(f"  Messages published: {self.messages_published}")
            logger.info(f"  Total time: {total_time:.1f}s")
            logger.info(f"  Actual rate: {actual_rate:.1f} msg/s")
            logger.info(f"  Target rate: {self.framerate:.1f} msg/s")
            logger.info(f"  Final tick: {self.current_tick}")
            
        except KeyboardInterrupt:
            logger.info("Replay interrupted by user")
        except Exception as e:
            logger.error(f"Error during replay: {e}")
            raise
    
    async def close(self) -> None:
        """Close NATS connection"""
        if self.nc:
            await self.nc.close()
            logger.info("NATS connection closed")
    
    async def run_replay(self, file_path: Path) -> None:
        """Run complete replay process"""
        try:
            self.load_capture_file(file_path)
            await self.connect()
            await self.replay_messages()
        finally:
            await self.close()
