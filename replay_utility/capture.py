"""
NATS Message Capture Module

Captures NATS messages from specified topics and saves them to JSON format
for later replay.
"""

import asyncio
import json
import logging
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Any, Optional

import nats
import orjson

from .config import ReplayConfig

logger = logging.getLogger(__name__)

class NATSCapture:
    """Captures NATS messages to JSON file"""
    
    def __init__(self, config: ReplayConfig):
        self.config = config
        self.nc: Optional[nats.NATS] = None
        self.messages: List[Dict[str, Any]] = []
        self.message_counts: Dict[str, int] = {}
        self.start_time: Optional[float] = None
        self.capture_duration: float = config.default_capture_duration
        
    async def connect(self) -> None:
        """Connect to NATS server"""
        try:
            self.nc = await nats.connect(self.config.nats_url)
            logger.info(f"Connected to NATS server: {self.config.nats_url}")
        except Exception as e:
            logger.error(f"Failed to connect to NATS: {e}")
            raise
    
    async def message_handler(self, msg) -> None:
        """Handle incoming NATS message"""
        try:
            # Parse message payload
            payload = orjson.loads(msg.data)
            
            # Create message record
            message_record = {
                "topic": msg.subject,
                "payload": payload,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "received_at": time.time()
            }
            
            # Store message
            self.messages.append(message_record)
            
            # Update topic counter
            topic = msg.subject
            self.message_counts[topic] = self.message_counts.get(topic, 0) + 1
            
            # Log progress every 100 messages
            total_messages = len(self.messages)
            if total_messages % 100 == 0:
                elapsed = time.time() - self.start_time if self.start_time else 0
                logger.info(f"Captured {total_messages} messages in {elapsed:.1f}s")
                
        except Exception as e:
            logger.error(f"Error processing message from {msg.subject}: {e}")
    
    async def subscribe_to_topics(self) -> None:
        """Subscribe to all capture topics"""
        if not self.nc:
            raise RuntimeError("Not connected to NATS")
        
        subscriptions = []
        for topic_pattern in self.config.capture_topics:
            try:
                sub = await self.nc.subscribe(topic_pattern, cb=self.message_handler)
                subscriptions.append(sub)
                logger.info(f"Subscribed to: {topic_pattern}")
            except Exception as e:
                logger.error(f"Failed to subscribe to {topic_pattern}: {e}")
                raise
        
        logger.info(f"Subscribed to {len(subscriptions)} topic patterns")
    
    async def capture_messages(self, duration: Optional[float] = None) -> None:
        """Capture messages for specified duration"""
        if duration:
            self.capture_duration = duration
        
        logger.info(f"Starting capture for {self.capture_duration} seconds...")
        self.start_time = time.time()
        
        # Subscribe to topics
        await self.subscribe_to_topics()
        
        # Capture for specified duration
        try:
            await asyncio.sleep(self.capture_duration)
        except KeyboardInterrupt:
            logger.info("Capture interrupted by user")
        
        # Calculate final statistics
        elapsed_time = time.time() - self.start_time
        total_messages = len(self.messages)
        
        logger.info(f"Capture completed:")
        logger.info(f"  Duration: {elapsed_time:.1f}s")
        logger.info(f"  Total messages: {total_messages}")
        logger.info(f"  Messages per second: {total_messages/elapsed_time:.1f}")
        
        # Log message counts by topic
        logger.info("Messages by topic:")
        for topic, count in sorted(self.message_counts.items()):
            logger.info(f"  {topic}: {count}")
    
    def save_to_json(self, output_path: Optional[Path] = None) -> Path:
        """Save captured messages to JSON file"""
        if not self.messages:
            raise ValueError("No messages captured")
        
        # Generate filename if not provided
        if output_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = self.config.get_capture_filename(timestamp)
        
        # Create capture metadata
        capture_metadata = {
            "capture_info": {
                "capture_time": datetime.now(timezone.utc).isoformat(),
                "duration_seconds": self.capture_duration,
                "total_messages": len(self.messages),
                "topics_captured": list(self.message_counts.keys()),
                "message_counts": self.message_counts,
                "remote_nats_url": self.config.nats_url
            },
            "messages": self.messages
        }
        
        # Save to JSON file
        try:
            with open(output_path, 'w') as f:
                json.dump(capture_metadata, f, indent=2)
            
            logger.info(f"Saved {len(self.messages)} messages to: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Failed to save JSON file: {e}")
            raise
    
    async def close(self) -> None:
        """Close NATS connection"""
        if self.nc:
            await self.nc.close()
            logger.info("NATS connection closed")
    
    async def run_capture(self, duration: Optional[float] = None, 
                         output_path: Optional[Path] = None) -> Path:
        """Run complete capture process"""
        try:
            await self.connect()
            await self.capture_messages(duration)
            saved_path = self.save_to_json(output_path)
            return saved_path
        finally:
            await self.close()
