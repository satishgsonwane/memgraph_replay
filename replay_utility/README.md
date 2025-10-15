# NATS Replay Utility

A self-contained utility for capturing NATS messages and replaying them locally at ticker speed with Memgraph bridge integration.

## Features

- **Capture Mode**: Subscribe to 6 NATS topics and save messages to JSON
- **Replay Mode**: Load captured messages and replay at framerate from `tickperframe`
- **Bridge Integration**: Automatically runs Memgraph bridge in background thread during replay
- **Timing Accuracy**: Maintains precise message timing based on original framerate
- **Graceful Shutdown**: Handles Ctrl+C and cleanup properly

## Quick Start

### Prerequisites

- Python 3.10+
- NATS server running on localhost:4222
- Memgraph database running on localhost:7687 (for bridge)

### Installation

The utility uses existing dependencies from the project. No additional installation required.

### Usage

#### Capture Messages

```bash
# Capture for 30 seconds (default)
python -m replay_utility capture

# Capture for custom duration
python -m replay_utility capture --duration 60

# Capture with custom output file
python -m replay_utility capture --duration 30 --output my_capture.json
```

#### Replay Messages

```bash
# Replay captured messages with bridge
python -m replay_utility replay --input captured_data/capture_20250127_120000.json
```

## Architecture

### Package Structure

```
replay_utility/
├── __init__.py          # Package initialization
├── capture.py           # NATS message capture to JSON
├── replay.py            # JSON replay to local NATS
├── runner.py            # CLI entry point with bridge integration
└── config.py            # Configuration settings

captured_data/           # Default directory for JSON files
└── .gitignore          # Ignore JSON files from git
```

### Key Components

#### 1. Capture Module (`capture.py`)
- Connects to NATS server (localhost:4222)
- Subscribes to 6 topic patterns:
  - `all_tracks.*`
  - `fused_players`
  - `fusion.ball_3d`
  - `intent.*`
  - `tickperframe`
  - `ptzinfo.*`
- Saves messages with metadata to timestamped JSON files
- Provides real-time progress indicators

#### 2. Replay Module (`replay.py`)
- Loads captured messages from JSON files
- Extracts framerate from `tickperframe` messages (default: 60 Hz)
- Publishes messages to local NATS (localhost:4222) at calculated rate
- Maintains timing accuracy and logs progress

#### 3. Runner Module (`runner.py`)
- CLI interface with `capture` and `replay` modes
- In replay mode:
  - Starts Memgraph bridge in background thread
  - Waits for bridge initialization
  - Runs replay publisher
  - Handles graceful shutdown (Ctrl+C)

#### 4. Configuration (`config.py`)
- Centralized configuration for NATS URLs and settings
- Automatic directory creation for captured data
- Input file validation

## JSON Format

Captured messages are saved in the following format:

```json
{
  "capture_info": {
    "capture_time": "2025-01-27T12:00:00Z",
    "duration_seconds": 30.0,
    "total_messages": 1500,
    "topics_captured": ["tickperframe", "all_tracks.camera1", ...],
    "message_counts": {
      "tickperframe": 30,
      "all_tracks.camera1": 300,
      ...
    },
    "remote_nats_url": "nats://localhost:4222"
  },
  "messages": [
    {
      "topic": "tickperframe",
      "payload": {"count": 1001, "framerate": 60.0},
      "timestamp": "2025-01-27T12:00:00Z",
      "received_at": 1737979200.0
    },
    ...
  ]
}
```

## Timing and Performance

### Message Timing
- Uses `asyncio.sleep()` for accurate timing between messages
- Calculates replay interval: `1.0 / framerate` seconds
- Accounts for processing time and logs timing drift if > 10ms

### Performance Features
- Uses `orjson` for fast JSON parsing
- Efficient message buffering during capture
- Real-time progress indicators
- Memory-conscious processing

## Error Handling

- Graceful NATS connection failure handling
- JSON file format validation
- Clear error messages for common issues
- Proper cleanup on exceptions and Ctrl+C
- Bridge thread management with timeout

## Testing

Run the test script to verify functionality:

```bash
python test_replay_utility.py
```

The test script will:
1. Test configuration settings
2. Test JSON format serialization
3. Test capture (if NATS server available)
4. Test replay (if local NATS available)

## Examples

### Complete Workflow

1. **Start required services**:
   ```bash
   # Terminal 1: Start NATS server
   nats-server
   
   # Terminal 2: Start Memgraph
   docker run -d --name memgraph_instance -p 7687:7687 memgraph/memgraph
   ```

2. **Capture messages**:
   ```bash
   python -m replay_utility capture --duration 30
   ```

3. **Replay messages**:
   ```bash
   python -m replay_utility replay --input captured_data/capture_20250127_120000.json
   ```

### Advanced Usage

```bash
# Capture with custom settings
python -m replay_utility capture --duration 120 --output long_capture.json

# Replay specific capture
python -m replay_utility replay --input long_capture.json
```

## Troubleshooting

### Common Issues

1. **NATS Connection Failed**
   - Ensure NATS server is running on correct port
   - Check firewall settings
   - Verify NATS URL in configuration

2. **Bridge Not Starting**
   - Ensure Memgraph is running on localhost:7687
   - Check database connection settings
   - Verify bridge configuration

3. **No Messages Captured**
   - Verify NATS server has active topics
   - Check topic patterns in configuration
   - Ensure sufficient capture duration

4. **Timing Drift During Replay**
   - Normal for high message rates
   - Consider reducing framerate for testing
   - Check system performance

### Debug Mode

Enable debug logging for detailed information:

```bash
export PYTHONPATH=.
python -c "
import logging
logging.basicConfig(level=logging.DEBUG)
import replay_utility.runner
replay_utility.runner.main()
" capture --duration 10
```

## Integration with OZ Game State Service

The replay utility integrates seamlessly with the existing OZ Game State Service:

- Uses the same `NATSMemgraphBridge` class
- Compatible with existing configuration
- Maintains same message processing pipeline
- Preserves all data relationships and TTL behavior

This makes it perfect for:
- **Development Testing**: Replay real data for development
- **Debugging**: Analyze specific game scenarios
- **Performance Testing**: Test with consistent data sets
- **Demo Purposes**: Show system behavior with real data
