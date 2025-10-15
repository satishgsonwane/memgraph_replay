# NATS-Memgraph Replay Utility

A high-performance bridge service that captures NATS messages and replays them to populate a Memgraph database with game state data. This project provides both a production-ready NATS-Memgraph bridge service and a comprehensive replay utility for testing and development.

## 🚀 Quick Start

### Prerequisites
- Python 3.10+
- Conda (Miniconda or Anaconda)
- Memgraph database running on localhost:7687
- NATS server running on localhost:4222

## NATS Server Setup

### For macOS (including Apple Silicon Macs):

1. **Install NATS server using Homebrew:**
   ```bash
   # Install Homebrew if you don't have it
   /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
   
   # Install NATS server
   brew install nats-server
   ```

2. **Start NATS server:**
   ```bash
   # Start NATS server on localhost:4222
   nats-server --port 4222
   
   # Or start in background
   nats-server --port 4222 &
   ```

3. **Verify NATS server is running:**
   ```bash
   # Check if NATS server is listening on port 4222
   lsof -i :4222
   
   # Or test connection
   telnet localhost 4222
   ```

### Alternative: Using Docker

If you prefer Docker:
```bash
# Run NATS server in Docker
docker run -d --name nats-server -p 4222:4222 nats:latest

# Check if it's running
docker ps | grep nats-server
```

### Quick Setup Scripts (macOS)

For easy setup on macOS, use the provided scripts:

```bash
# Automated setup (installs Homebrew, NATS server, and starts it)
./scripts/setup/setup_nats_macos.sh

# Manage NATS server (start/stop/status/test)
./scripts/tools/nats_manager.sh start    # Start NATS server
./scripts/tools/nats_manager.sh status   # Check status
./scripts/tools/nats_manager.sh test     # Test connection
./scripts/tools/nats_manager.sh stop     # Stop NATS server
```

**Note**: If you already have Memgraph running, you only need to set up NATS server!

### Environment Setup
```bash
# Create and setup conda environment
./setup_conda_env.sh

# Activate the environment
./activate_env.sh
# OR
conda activate memgraph_replay
```

### Project Setup
```bash
# Initialize USD scene structure
python scripts/setup/init_usd_scene.py

# Run automated test sequence
./run_test_sequence.sh
```

### Manual Usage
```bash
# Start the bridge service
python memgraph_skg.py

# Capture NATS messages
python -m replay_utility capture

# Replay captured data (default: continuous loop with topic-specific rates)
python -m replay_utility replay --input data/captured/my_capture.json

# Replay options:
# --no-loop: Single replay instead of continuous loop
# --no-topic-rates: Use global framerate instead of topic-specific rates
```

## 📁 Project Structure

- **`src/`** - Core application code (services, processors, utils)
- **`replay_utility/`** - Message capture and replay functionality
- **`database/`** - Database interface layer
- **`scripts/`** - Setup and utility tools
- **`data/`** - Captured data and configuration
- **`tests/`** - Test suites and examples
- **`docs/`** - Documentation

See [PROJECT_STRUCTURE.md](docs/PROJECT_STRUCTURE.md) for detailed structure information.

## 🎯 Key Features

### Core Bridge Service
- **High-Performance**: Sub-10ms P95 latency with ultra-low latency batch processing (5ms intervals)
- **Time-Based TTL**: Automatic data cleanup with configurable retention (30-second sliding window)
- **USD Schema**: Persistent game state with Scene_Descriptor structure
- **Relationship Management**: Proper node relationships for CameraConfig, FusedPlayer, and FusionBall3D
- **Connection Pooling**: 15 database connections for high throughput
- **Message Deduplication**: Intelligent caching to prevent duplicates

### Replay Utility
- **Capture Mode**: Subscribe to 6 NATS topics and save messages to JSON
- **Replay Mode**: Load captured messages and replay with intelligent defaults
- **Bridge Integration**: Automatically runs Memgraph bridge in background thread during replay
- **Timing Accuracy**: Maintains precise message timing based on original framerate
- **Topic-Specific Rates**: Realistic replay rates per topic (enabled by default)
- **Continuous Replay**: Loop mode for continuous testing (enabled by default)
- **Graceful Shutdown**: Handles Ctrl+C and cleanup properly

## 🔗 Node Relationships

The system creates these key relationships in Memgraph:
- `Scene_Descriptor` → `CameraConfig` (HAS_CAMERA)
- `Scene_Descriptor` → `FusedPlayer` (HAS_PLAYER)  
- `Scene_Descriptor` → `FusionBall3D` (HAS_BALL)
- `CameraConfig` → `Intent` (HAS_INTENT)

## 📊 Performance

### Bridge Service Performance
- **Batch Processing**: 5ms intervals for ultra-low latency
- **Connection Pooling**: 15 database connections for high throughput
- **TTL Cleanup**: 1-second intervals for data retention management
- **Message Deduplication**: Intelligent caching to prevent duplicates
- **Query Timeout**: 50ms maximum query time to prevent blocking

### Replay Utility Performance
- **Timing Accuracy**: Maintains precise message timing based on original framerate
- **Topic-Specific Rates**: Each topic replays at its configured rate for realistic testing
- **Memory Efficient**: Uses orjson for fast JSON parsing
- **Background Processing**: Bridge runs in separate thread during replay

## 🛠️ Development

### Tools
```bash
# Check USD nodes in database
python3 scripts/tools/check_usd_nodes.py

# Monitor USD persistence
python3 scripts/tools/monitor_usd_persistence.py

# Debug scene relationships
python3 scripts/tools/fix_usd_relationships.py
```

### Testing
```bash
# Run complete test sequence (default: continuous loop with topic-specific rates)
./run_test_sequence.sh

# Test sequence options:
# --no-loop: Single replay instead of continuous loop
# --no-topic-rates: Use global framerate instead of topic-specific rates

# Run individual tests
python3 tests/test_replay_utility.py

# Test options:
# --no-loop: Disable loop mode
# --no-topic-rates: Disable topic-specific rates

# Test environment setup
python3 test_environment.py
```

## 📚 Documentation

- [Project Structure](docs/PROJECT_STRUCTURE.md) - Detailed directory organization
- [Test Sequence](docs/README_TEST_SEQUENCE.md) - Automated testing guide
- [Implementation Summary](docs/IMPLEMENTATION_SUMMARY.md) - Technical overview
- [macOS Setup Guide](docs/SETUP_MACOS.md) - Complete setup guide for macOS (including Apple Silicon)

## ⚙️ Configuration

Configuration is centralized in `src/core/config.py` with:

### Connection Settings
- **NATS URL**: `nats://localhost:4222`
- **Memgraph Host**: `localhost:7687`
- **Connection Pool**: 15 connections for high throughput

### Performance Tuning
- **Batch Interval**: 5ms for ultra-low latency
- **Max Batch Size**: 200 messages per batch
- **Query Timeout**: 50ms maximum query time
- **Connection Timeout**: 100ms connection establishment

### TTL and Cleanup
- **Rolling Window**: 30 seconds data retention
- **Cleanup Interval**: 1 second cleanup frequency
- **Max Cleanup Time**: 50ms maximum cleanup duration

### Topic Filtering
- Filters low-value topics (`fps.*`, `colour-control.*`, `camera_mode_entry.*`)
- Focuses processing on high-value game state data

## 🐍 Environment Management

### Creating Environment
```bash
# Option 1: Automated setup script (recommended)
./setup_conda_env.sh

# Option 2: Using environment.yml
conda env create -f environment.yml

# Option 3: Manual setup
conda create -n memgraph_replay python=3.10
conda activate memgraph_replay
pip install -r requirements.txt
```

### Activating Environment
```bash
# Quick activation
./activate_env.sh

# Manual activation
conda activate memgraph_replay
```

### Managing Environment
```bash
# List environments
conda env list

# Update packages
conda activate memgraph_replay
pip install -r requirements.txt --upgrade

# Remove environment
conda env remove -n memgraph_replay
```

## 🔧 Troubleshooting

Common issues and solutions:
- **Missing Scene_Descriptor**: Run `scripts/setup/init_usd_scene.py`
- **No relationships**: Check USD initialization and message processing
- **Performance issues**: Verify connection pooling and batch settings
- **Processes won't stop**: Run `scripts/tools/cleanup_processes.sh` to force stop all processes

### Process Cleanup
If Ctrl+C doesn't properly stop all processes:
```bash
# Manual cleanup script
./scripts/tools/cleanup_processes.sh

# Or force kill all related processes
pkill -f "memgraph_skg.py|test_replay_utility.py|replay_utility"
```

See individual tool documentation for specific debugging guidance.
