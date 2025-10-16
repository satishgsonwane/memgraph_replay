# Environment Setup

This directory contains the environment setup for the NATS-Memgraph Replay Utility.

## Quick Setup

```bash
# Run the setup script
./setup_env.sh

# Activate the environment
./activate_env.sh

# Test everything works
python test_environment.py
```

## Files

- **`setup_env.sh`** - Main setup script (cross-platform, supports Linux, macOS Intel & Apple Silicon)
- **`activate_env.sh`** - Quick activation script
- **`test_environment.py`** - Test all dependencies
- **`environment.yml`** - Conda environment specification
- **`requirements.txt`** - Python package requirements

## Dependencies

- **nats-server** - NATS messaging server
- **mgclient** (via pymgclient) - Memgraph Python client
- **nats-py** - NATS async client
- **orjson** - Fast JSON library
- **pydantic** - Data validation
- **tenacity** - Retry library
- **filterpy** - Signal processing
- **numpy/pandas** - Data processing
- **psutil** - System utilities

## Architecture Support

- ✅ Linux x86_64
- ✅ Linux ARM64
- ✅ macOS Intel (x86_64)
- ✅ macOS Apple Silicon (ARM64)

The setup script automatically detects your architecture and downloads the correct NATS server binary.
