# Project Structure

This document describes the organized structure of the NATS-Memgraph Replay Utility project.

## 📁 Directory Structure

```
memgraph_replay_utility/
├── src/                          # Main source code
│   ├── core/                     # Core services and configuration
│   │   ├── __init__.py
│   │   ├── config.py             # Bridge configuration and defaults
│   │   ├── interfaces.py         # Database and service interfaces
│   │   └── service.py            # Main NATS-Memgraph bridge service
│   ├── processors/               # Data processing components
│   │   ├── __init__.py
│   │   ├── batch_processor.py    # Message batch processing
│   │   ├── cleanup_manager.py    # TTL-based data cleanup
│   │   ├── cypher_builder.py     # NATS message to Cypher conversion
│   │   └── query_executor.py     # Database query execution
│   ├── schema/                   # Data schemas and contracts
│   │   ├── __init__.py
│   │   └── contracts.py          # Pydantic models for data validation
│   └── utils/                    # Utility functions
│       ├── __init__.py
│       ├── cache.py              # Message caching for deduplication
│       ├── metrics.py            # Performance metrics collection
│       └── scene_initializer.py  # USD scene structure initialization
├── replay_utility/               # Replay functionality
│   ├── __init__.py
│   ├── __main__.py              # CLI entry point
│   ├── capture.py               # NATS message capture
│   ├── config.py                # Replay configuration
│   ├── replay.py                # Message replay functionality
│   ├── runner.py                # Bridge management for replay
│   └── README.md                # Replay utility documentation
├── database/                     # Database layer
│   ├── __init__.py
│   └── repository.py            # Memgraph database interface
├── scripts/                      # Standalone scripts
│   ├── setup/                   # Setup and initialization scripts
│   │   └── init_usd_scene.py    # USD scene initialization script
│   └── tools/                   # Utility tools
│       ├── check_usd_nodes.py   # USD nodes verification
│       ├── debug_scene_deletion.py # Scene debugging
│       ├── fix_usd_relationships.py # Relationship repair
│       ├── monitor_usd_persistence.py # USD persistence monitoring
│       ├── query_recent_tracks_by_camera.py # Camera track queries
│       └── track_queries.py     # Track analysis queries
├── data/                         # Data files
│   ├── captured/                 # Captured NATS data
│   │   └── my_capture.json      # Sample captured data
│   ├── config/                   # Configuration data
│   │   └── gen_pitch_data_standalone.py # Standalone pitch data
│   └── .gitignore               # Data directory gitignore
├── logs/                         # Log files
│   ├── memgraph_skg.log         # Bridge service logs
│   ├── memgraph_skg.pid         # Process ID file
│   └── test_replay.log          # Test execution logs
├── docs/                         # Documentation
│   ├── IMPLEMENTATION_SUMMARY.md # Implementation overview
│   ├── PROJECT_STRUCTURE.md     # This file
│   └── README_TEST_SEQUENCE.md  # Test sequence documentation
├── tests/                        # Test files
│   ├── example_replay_usage.py  # Example usage script
│   └── test_replay_utility.py   # Main test suite
├── memgraph_skg.py              # Main service entry point
└── run_test_sequence.sh         # Automated test runner
```

## 🎯 Component Overview

### Core Components (`src/core/`)
- **config.py**: Centralized configuration with time-based TTL settings
- **interfaces.py**: Abstract interfaces for dependency injection
- **service.py**: Main NATS-Memgraph bridge with async processing

### Processing Pipeline (`src/processors/`)
- **cypher_builder.py**: Converts NATS messages to Cypher queries
- **query_executor.py**: Executes database operations with relationships
- **batch_processor.py**: Manages message batching for performance
- **cleanup_manager.py**: Handles TTL-based data retention

### Utilities (`src/utils/`)
- **cache.py**: Message deduplication and caching
- **metrics.py**: Performance monitoring and statistics
- **scene_initializer.py**: USD scene structure setup

### Replay System (`replay_utility/`)
- **capture.py**: Captures NATS messages to JSON files
- **replay.py**: Replays captured messages to test systems
- **runner.py**: Manages bridge lifecycle during replay

### Database Layer (`database/`)
- **repository.py**: Memgraph connection and query management

### Scripts (`scripts/`)
- **setup/**: Initialization and setup utilities
- **tools/**: Analysis and debugging tools

## 🔗 Key Relationships

### Data Flow
1. **Capture**: NATS messages → JSON files (`data/captured/`)
2. **Replay**: JSON files → NATS messages → Memgraph
3. **Processing**: NATS messages → Cypher queries → Database

### Node Relationships
- **Scene_Descriptor** ←→ **CameraConfig** (HAS_CAMERA)
- **Scene_Descriptor** ←→ **FusedPlayer** (HAS_PLAYER)
- **Scene_Descriptor** ←→ **FusionBall3D** (HAS_BALL)
- **CameraConfig** ←→ **Intent** (HAS_INTENT)

## 🚀 Usage Patterns

### Development
```bash
# Initialize USD scene
python3 scripts/setup/init_usd_scene.py

# Check USD nodes
python3 scripts/tools/check_usd_nodes.py

# Run tests
./run_test_sequence.sh
```

### Production
```bash
# Start service
python3 memgraph_skg.py

# Capture data
python3 -m replay_utility.capture

# Replay data
python3 -m replay_utility.replay data/captured/my_capture.json
```

## 📋 File Purposes

### Required Files
- `memgraph_skg.py` - Main service entry point
- `src/` - Core application code
- `database/repository.py` - Database interface
- `replay_utility/` - Replay functionality

### Optional Files
- `scripts/` - Development and debugging tools
- `tests/` - Test suites and examples
- `docs/` - Documentation
- `logs/` - Runtime logs

### Data Files
- `data/captured/` - Captured NATS messages
- `data/config/` - Configuration and pitch data

This structure provides clear separation of concerns, easy navigation, and maintainable code organization.
