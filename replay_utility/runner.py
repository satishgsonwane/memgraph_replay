"""
NATS Replay Utility CLI Runner

Main entry point for the NATS replay utility with CLI interface
and Memgraph bridge integration.
"""

import argparse
import asyncio
import logging
import signal
import sys
import threading
import time
from pathlib import Path
from typing import Optional

from .capture import NATSCapture
from .replay import NATSReplay
from .config import ReplayConfig

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class BridgeManager:
    """Manages Memgraph bridge in separate thread"""
    
    def __init__(self):
        self.bridge_thread: Optional[threading.Thread] = None
        self.bridge = None
        self.shutdown_event = threading.Event()
        self.bridge_ready = threading.Event()
        
    def start_bridge(self) -> None:
        """Start Memgraph bridge in background thread"""
        logger.info("Starting Memgraph bridge in background thread...")
        
        def run_bridge():
            """Run bridge in separate asyncio event loop"""
            try:
                # Import here to avoid circular imports
                from src.core.service import NATSMemgraphBridge
                from src.core.config import BridgeConfig
                
                # Create bridge configuration for local NATS
                config = BridgeConfig()
                config.nats_url = "nats://localhost:4222"  # Force local NATS
                
                # Create bridge instance
                self.bridge = NATSMemgraphBridge(config)
                
                # Run bridge
                asyncio.run(self._run_bridge_async())
                
            except Exception as e:
                logger.error(f"Bridge thread error: {e}")
                import traceback
                logger.error(f"Bridge traceback: {traceback.format_exc()}")
        
        # Start bridge thread
        self.bridge_thread = threading.Thread(target=run_bridge, daemon=True)
        self.bridge_thread.start()
        
        # Wait for bridge to be ready
        logger.info("Waiting for bridge initialization...")
        from .config import ReplayConfig
        config = ReplayConfig()
        time.sleep(config.bridge_startup_delay)  # Use configurable delay
        logger.info("Bridge should be ready for message processing")
    
    async def _run_bridge_async(self) -> None:
        """Run bridge async operations"""
        try:
            async with self.bridge:
                self.bridge_ready.set()
                await self.bridge.run()
        except Exception as e:
            logger.error(f"Bridge async error: {e}")
            raise
    
    def stop_bridge(self) -> None:
        """Stop the bridge gracefully"""
        if self.bridge_thread and self.bridge_thread.is_alive():
            logger.info("Stopping Memgraph bridge...")
            self.shutdown_event.set()
            
            # Give bridge time to shutdown
            self.bridge_thread.join(timeout=5.0)
            
            if self.bridge_thread.is_alive():
                logger.warning("Bridge thread did not stop gracefully")
            else:
                logger.info("Bridge stopped successfully")

def setup_signal_handlers(bridge_manager: BridgeManager) -> None:
    """Setup signal handlers for graceful shutdown"""
    def signal_handler(signum, frame):
        logger.info(f"Received signal {signum}, shutting down...")
        bridge_manager.stop_bridge()
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

async def run_capture_mode(args) -> None:
    """Run capture mode"""
    config = ReplayConfig()
    capture = NATSCapture(config)
    
    try:
        output_path = None
        if args.output:
            # Ensure output file goes to captured_data directory
            output_filename = Path(args.output).name
            output_path = config.captured_data_dir / output_filename
        
        saved_path = await capture.run_capture(
            duration=args.duration,
            output_path=output_path
        )
        
        logger.info(f"Capture completed successfully: {saved_path}")
        
    except Exception as e:
        logger.error(f"Capture failed: {e}")
        sys.exit(1)

async def run_replay_mode(args) -> None:
    """Run replay mode with bridge integration"""
    config = ReplayConfig()
    
    # Validate input file
    try:
        input_path = config.validate_input_file(args.input)
    except Exception as e:
        logger.error(f"Input file error: {e}")
        sys.exit(1)
    
    # Start bridge manager
    bridge_manager = BridgeManager()
    setup_signal_handlers(bridge_manager)
    
    try:
        # Start Memgraph bridge in background
        bridge_manager.start_bridge()
        
        # Create replay instance
        replay = NATSReplay(config, loop=not args.no_loop, topic_specific_rates=not args.no_topic_rates)
        
        # Run replay
        await replay.run_replay(input_path)
        
        logger.info("Replay completed successfully")
        
    except KeyboardInterrupt:
        logger.info("Replay interrupted by user")
    except Exception as e:
        logger.error(f"Replay failed: {e}")
        sys.exit(1)
    finally:
        # Stop bridge
        bridge_manager.stop_bridge()

def main() -> None:
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description="NATS Replay Utility - Capture and replay NATS messages",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Capture messages for 30 seconds
  python -m replay_utility capture --duration 30
  
  # Capture with custom output filename (saved in captured_data/)
  python -m replay_utility capture --duration 60 --output my_capture.json
  
  # Replay captured messages with bridge (default: loop + topic-specific rates)
  python -m replay_utility replay --input captured_data/capture_20250127_120000.json
  
  # Disable loop mode (single replay)
  python -m replay_utility replay --input captured_data/capture_20250127_120000.json --no-loop
  
  # Disable topic-specific rates (use global framerate)
  python -m replay_utility replay --input captured_data/capture_20250127_120000.json --no-topic-rates
  
  # Disable both (single replay with global framerate)
  python -m replay_utility replay --input captured_data/capture_20250127_120000.json --no-loop --no-topic-rates
        """
    )
    
    subparsers = parser.add_subparsers(dest='mode', help='Operation mode')
    
    # Capture mode
    capture_parser = subparsers.add_parser('capture', help='Capture NATS messages')
    capture_parser.add_argument(
        '--duration', '-d',
        type=float,
        default=30.0,
        help='Capture duration in seconds (default: 30)'
    )
    capture_parser.add_argument(
        '--output', '-o',
        type=str,
        help='Output JSON filename (saved in captured_data/ directory, default: auto-generated timestamp)'
    )
    
    # Replay mode
    replay_parser = subparsers.add_parser('replay', help='Replay captured messages')
    replay_parser.add_argument(
        '--input', '-i',
        type=str,
        required=True,
        help='Input JSON file path'
    )
    replay_parser.add_argument(
        '--no-loop',
        action='store_true',
        help='Disable loop mode (default: loop enabled)'
    )
    replay_parser.add_argument(
        '--no-topic-rates',
        action='store_true',
        help='Disable topic-specific rates (default: topic-specific rates enabled)'
    )
    
    # Parse arguments
    args = parser.parse_args()
    
    if not args.mode:
        parser.print_help()
        sys.exit(1)
    
    # Run appropriate mode
    try:
        if args.mode == 'capture':
            asyncio.run(run_capture_mode(args))
        elif args.mode == 'replay':
            asyncio.run(run_replay_mode(args))
        else:
            parser.print_help()
            sys.exit(1)
            
    except KeyboardInterrupt:
        logger.info("Operation interrupted by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
