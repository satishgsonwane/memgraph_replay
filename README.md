# NATS-Memgraph Replay Utility

A high-performance bridge service that captures NATS messages and replays them to populate a Memgraph database with game state data.

## 🚀 Quick Start

### 1. Setup Environment
```bash
# Automated setup (cross-platform)
./setup_env.sh

# Activate environment
./activate_env.sh

# Test installation
python test_environment.py
```

### 2. Start Services
```bash
# Start NATS server (separate terminal)
nats-server --port 4222 --http_port 8222

# Start Memgraph (Docker)
docker run -d --name memgraph -p 7687:7687 memgraph/memgraph
```

### 3. Run Tests
```bash
# Initialize USD scene
python scripts/setup/init_usd_scene.py

# Run automated test sequence
./run_test_sequence.sh
```

## 📋 Usage

### Bridge Service
```bash
# Start the production bridge
python memgraph_skg.py
```

### Capture & Replay
```bash
# Capture NATS messages (30 seconds)
python -m replay_utility capture

# Replay with bridge integration
python -m replay_utility replay --input data/captured/my_capture.json

# Replay options:
# --no-loop: Single replay instead of continuous loop
# --no-topic-rates: Use global framerate instead of topic-specific rates
```

## 🎯 Key Features

- **High-Performance Bridge**: Sub-10ms P95 latency with 5ms batch processing
- **Time-Based TTL**: 30-second rolling window with automatic cleanup
- **USD Schema**: Persistent game state with Scene_Descriptor structure
- **Message Capture**: Subscribe to 6 NATS topics and save to JSON
- **Intelligent Replay**: Topic-specific rates with timing accuracy
- **Bridge Integration**: Automatic background bridge during replay

## 🔗 Data Relationships

- `Scene_Descriptor` → `CameraConfig` (HAS_CAMERA)
- `Scene_Descriptor` → `FusedPlayer` (HAS_PLAYER)  
- `Scene_Descriptor` → `FusionBall3D` (HAS_BALL)
- `CameraConfig` → `Intent` (HAS_INTENT)

## 🛠️ Development Tools

```bash
# Check USD nodes
python scripts/tools/check_usd_nodes.py

# Monitor persistence
python scripts/tools/monitor_usd_persistence.py

# Debug relationships
python scripts/tools/fix_usd_relationships.py

# Cleanup processes
./scripts/tools/cleanup_processes.sh
```

## 📊 Performance

- **Batch Processing**: 5ms intervals
- **Connection Pool**: 15 database connections
- **TTL Cleanup**: 1-second intervals
- **Query Timeout**: 50ms maximum
- **Message Deduplication**: Intelligent caching

## 🔧 Troubleshooting

- **Missing Scene_Descriptor**: Run `scripts/setup/init_usd_scene.py`
- **Process cleanup**: Use `./scripts/tools/cleanup_processes.sh`
- **Environment issues**: Run `python test_environment.py`

## 📚 Documentation

- [Test Sequence Guide](README_TEST_SEQUENCE.md) - Automated testing
- [Environment Setup](ENVIRONMENT_SETUP.md) - Setup details

## ⚙️ Configuration

Configuration is in `src/core/config.py`:
- **NATS URL**: `nats://localhost:4222`
- **Memgraph**: `localhost:7687`
- **Batch Interval**: 5ms
- **TTL Window**: 30 seconds
- **Connection Pool**: 15 connections