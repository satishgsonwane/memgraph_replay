#!/usr/bin/env python3
"""
Generate and send NATS intent messages for different cameras at 6 messages per second.

This script creates intent messages based on the provided examples and distributes them
across different cameras (camera1-camera6) to simulate realistic camera intent processing.
"""

import asyncio
import json
import logging
import time
import uuid
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional
from pathlib import Path

import nats
import orjson

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class IntentMessageGenerator:
    """Generate and send intent messages for different cameras"""
    
    def __init__(self, nats_url: str = "nats://localhost:4222"):
        self.nats_url = nats_url
        self.nc: Optional[nats.NATS] = None
        self.messages_sent = 0
        self.start_time: Optional[float] = None
        
    async def connect(self) -> None:
        """Connect to NATS server"""
        try:
            self.nc = await nats.connect(self.nats_url)
            logger.info(f"Connected to NATS server: {self.nats_url}")
        except Exception as e:
            logger.error(f"Failed to connect to NATS: {e}")
            raise
    
    def generate_intent_messages(self) -> List[Dict[str, Any]]:
        """Generate intent messages based on the provided examples"""
        
        # Base messages from the user's examples
        base_messages = [
            {
                "status": "expired",
                "intent_id": "superseded",
                "intent_type": "unknown",
                "resolved_ttl_ms": None,
                "payload": None,
                "rule_definition": None,
                "reason": "SUPERSEDED"
            },
            {
                "status": "active",
                "intent_id": "74c7211b-1032-4739-a5c2-9483970c6002",
                "intent_type": "nudge_tilt",
                "resolved_ttl_ms": 5000,
                "payload": {"offset_level": "L1", "direction": "1"},
                "rule_definition": {"action": "offset_current_target", "axis": "tilt", "default_ttl_level": "L3"},
                "reason": None
            },
            {
                "status": "expired",
                "intent_id": "superseded",
                "intent_type": "unknown",
                "resolved_ttl_ms": None,
                "payload": None,
                "rule_definition": None,
                "reason": "SUPERSEDED"
            },
            {
                "status": "active",
                "intent_id": "e8923fba-7030-4c7c-851a-98b04addb11a",
                "intent_type": "nudge_pan",
                "resolved_ttl_ms": 5000,
                "payload": {"offset_level": "L2", "direction": "-1"},
                "rule_definition": {"action": "offset_current_target", "axis": "pan", "default_ttl_level": "L3"},
                "reason": None
            },
            {
                "status": "expired",
                "intent_id": "e8923fba-7030-4c7c-851a-98b04addb11a",
                "intent_type": "nudge_pan",
                "resolved_ttl_ms": None,
                "payload": None,
                "rule_definition": None,
                "reason": "TTL_EXPIRED"
            },
            {
                "status": "active",
                "intent_id": "27797a0e-61fb-4892-b3ca-e9429d061b0e",
                "intent_type": "none",
                "resolved_ttl_ms": 10000,
                "payload": {"offset_level": "L1", "direction": "1"},
                "rule_definition": {},
                "reason": None
            }
        ]
        
        # Additional intent types for variety
        additional_intents = [
            {
                "status": "active",
                "intent_type": "nudge_zoom",
                "resolved_ttl_ms": 3000,
                "payload": {"offset_level": "L3", "direction": "1"},
                "rule_definition": {"action": "offset_current_target", "axis": "zoom", "default_ttl_level": "L2"},
                "reason": None
            },
            {
                "status": "active",
                "intent_type": "track_player",
                "resolved_ttl_ms": 8000,
                "payload": {"player_id": "player_123", "track_mode": "follow"},
                "rule_definition": {"action": "track_target", "target_type": "player", "default_ttl_level": "L1"},
                "reason": None
            },
            {
                "status": "active",
                "intent_type": "track_ball",
                "resolved_ttl_ms": 6000,
                "payload": {"track_mode": "smooth", "prediction": True},
                "rule_definition": {"action": "track_target", "target_type": "ball", "default_ttl_level": "L2"},
                "reason": None
            },
            {
                "status": "expired",
                "intent_type": "unknown",
                "resolved_ttl_ms": None,
                "payload": None,
                "rule_definition": None,
                "reason": "MANUAL_OVERRIDE"
            }
        ]
        
        # Combine all messages
        all_messages = base_messages + additional_intents
        
        # Generate messages for each camera
        messages = []
        cameras = ["camera1", "camera2", "camera3", "camera4", "camera5", "camera6"]
        
        for i, base_msg in enumerate(all_messages):
            for camera_id in cameras:
                # Create a copy of the base message
                msg = base_msg.copy()
                
                # Assign camera_id
                msg["camera_id"] = camera_id
                
                # Generate unique intent_id for active intents
                if msg["status"] == "active" and msg.get("intent_id") != "superseded":
                    msg["intent_id"] = str(uuid.uuid4())
                
                # Add timestamp
                msg["timestamp"] = datetime.now(timezone.utc).isoformat()
                
                messages.append(msg)
        
        logger.info(f"Generated {len(messages)} intent messages for {len(cameras)} cameras")
        return messages
    
    async def send_message(self, message: Dict[str, Any]) -> None:
        """Send a single intent message to NATS"""
        if not self.nc:
            raise RuntimeError("Not connected to NATS")
        
        try:
            topic = "intents.processed"
            # Remove timestamp from payload since it's not part of the original schema
            payload = {k: v for k, v in message.items() if k != 'timestamp'}
            payload_bytes = orjson.dumps(payload)
            
            await self.nc.publish(topic, payload_bytes)
            self.messages_sent += 1
            
            # Log progress every 10 messages
            if self.messages_sent % 10 == 0:
                elapsed = time.time() - self.start_time if self.start_time else 0
                rate = self.messages_sent / elapsed if elapsed > 0 else 0
                logger.info(f"Sent {self.messages_sent} messages (rate: {rate:.1f} msg/s)")
                
        except Exception as e:
            logger.error(f"Failed to send message: {e}")
            raise
    
    async def send_messages_at_rate(self, messages: List[Dict[str, Any]], rate: float = 6.0) -> None:
        """Send messages at specified rate (messages per second)"""
        if not messages:
            logger.warning("No messages to send")
            return
        
        interval = 1.0 / rate  # Time between messages in seconds
        logger.info(f"Sending {len(messages)} messages at {rate} msg/s (interval: {interval:.3f}s)")
        
        self.start_time = time.time()
        
        for i, message in enumerate(messages):
            await self.send_message(message)
            
            # Calculate timing for next message
            if i < len(messages) - 1:  # Don't sleep after last message
                target_time = self.start_time + (i + 1) * interval
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
        
        # Log final statistics
        total_time = time.time() - self.start_time
        actual_rate = self.messages_sent / total_time
        logger.info(f"Completed sending {self.messages_sent} messages")
        logger.info(f"Total time: {total_time:.1f}s")
        logger.info(f"Actual rate: {actual_rate:.1f} msg/s")
    
    async def close(self) -> None:
        """Close NATS connection"""
        if self.nc:
            await self.nc.close()
            logger.info("NATS connection closed")
    
    async def run(self, rate: float = 6.0) -> None:
        """Run the complete message generation and sending process"""
        try:
            await self.connect()
            messages = self.generate_intent_messages()
            await self.send_messages_at_rate(messages, rate)
        finally:
            await self.close()

async def main():
    """Main function to run the intent message generator"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Generate and send NATS intent messages")
    parser.add_argument("--rate", type=float, default=6.0, 
                       help="Message rate in messages per second (default: 6.0)")
    parser.add_argument("--nats-url", type=str, default="nats://localhost:4222",
                       help="NATS server URL (default: nats://localhost:4222)")
    parser.add_argument("--save-messages", action="store_true",
                       help="Save generated messages to JSON file")
    parser.add_argument("--output-file", type=str, default="generated_intent_messages.json",
                       help="Output file for saved messages (default: generated_intent_messages.json)")
    
    args = parser.parse_args()
    
    generator = IntentMessageGenerator(nats_url=args.nats_url)
    
    # Generate messages
    messages = generator.generate_intent_messages()
    
    # Save messages to file if requested
    if args.save_messages:
        output_path = Path(args.output_file)
        with open(output_path, 'w') as f:
            json.dump(messages, f, indent=2)
        logger.info(f"Saved {len(messages)} messages to {output_path}")
    
    # Send messages
    await generator.run(rate=args.rate)

if __name__ == "__main__":
    asyncio.run(main())
