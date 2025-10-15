#!/usr/bin/env python3
"""
Main entry point for the OZ Game State Service
"""

import asyncio
import os
import signal
import subprocess
import sys
from src.core.service import NATSMemgraphBridge
from src.core.config import BridgeConfig

async def check_memgraph_health():
    """Check if Memgraph is ready to accept connections"""
    import mgclient
    from src.core.config import MEMGRAPH_HOST, MEMGRAPH_PORT
    
    max_attempts = 10
    for attempt in range(max_attempts):
        try:
            print(f"Checking Memgraph health (attempt {attempt + 1}/{max_attempts})...")
            conn = mgclient.connect(host=MEMGRAPH_HOST, port=MEMGRAPH_PORT)
            conn.close()
            print("Memgraph is ready and accepting connections")
            return True
        except Exception as e:
            print(f"Memgraph not ready yet: {e}")
            if attempt < max_attempts - 1:
                await asyncio.sleep(3)  # Wait 3 seconds between attempts
            else:
                print("Memgraph failed to become ready after all attempts")
                return False
    return False

async def restart_memgraph():
    """Restart the oz-memgraph Docker container using memdocker.sh script and wait for it to be ready"""
    try:
        print("Restarting oz-memgraph Docker container using memdocker.sh...")
        
        # Get the path to the memdocker.sh script
        script_path = os.path.join(os.path.dirname(__file__), "scripts", "memdocker.sh")
        
        # Make sure the script is executable
        os.chmod(script_path, 0o755)
        
        result = subprocess.run(
            [script_path],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode == 0:
            print("Successfully restarted oz-memgraph container")
            print("Waiting for Memgraph to be ready...")
            
            # Wait for Memgraph to be ready with health checks
            if await check_memgraph_health():
                print("Memgraph is ready, proceeding with service startup")
                return True
            else:
                print("Memgraph health check failed, but continuing anyway...")
                return False
        else:
            print(f"Failed to restart oz-memgraph container: {result.stderr}")
            return False
    except subprocess.TimeoutExpired:
        print("Timeout while restarting oz-memgraph container")
        return False
    except Exception as e:
        print(f"Error restarting oz-memgraph container: {e}")
        return False

async def main():
    """Main application entry point"""
    # Restart Memgraph container before starting
    print("🚀 Starting OZ Game State Service...")
    if not await restart_memgraph():
        print("Memgraph restart failed, but continuing with service startup...")
        print("The service will attempt to connect with its built-in retry logic")
    
    # Create configuration
    config = BridgeConfig()
    
    # Create bridge instance
    print("🔧 Initializing bridge components...")
    bridge = NATSMemgraphBridge(config)
    
    # Setup signal handlers for graceful shutdown
    def signal_handler(signum, frame):
        print(f"\nReceived signal {signum}, shutting down gracefully...")
        asyncio.create_task(bridge.shutdown())
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        # Run the bridge
        async with bridge:
            await bridge.run()
    except KeyboardInterrupt:
        print("\nShutdown requested by user")
    except Exception as e:
        print(f"Error running bridge: {e}")
        sys.exit(1)
    finally:
        await bridge.close()

if __name__ == "__main__":
    asyncio.run(main()) 