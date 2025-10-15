# macOS Setup Guide

Complete setup guide for running the NATS-Memgraph Replay Utility on macOS (including Apple Silicon Macs).

## 🚀 Quick Start (Recommended)

### 1. Automated Setup
```bash
# Clone the repository (if not already done)
git clone <your-repo-url>
cd memgraph_replay_utility

# Run automated setup script
./scripts/setup/setup_nats_macos.sh
```

This script will:
- ✅ Check if you're on macOS
- ✅ Install Homebrew (if not present)
- ✅ Install NATS server via Homebrew
- ✅ Start NATS server on localhost:4222
- ✅ Test the connection
- ✅ Show status and next steps

### 2. Setup Conda Environment
```bash
# Create and setup conda environment
./setup_conda_env.sh

# Activate the environment
./activate_env.sh
```

### 3. Verify Memgraph (if not already running)
```bash
# Check if Memgraph is already running
docker ps | grep memgraph

# If not running, start Memgraph using Docker
docker run -d --name memgraph -p 7687:7687 memgraph/memgraph

# Verify it's running
docker ps | grep memgraph
```

### 4. Run the Test Sequence
```bash
# Run complete automated test
./run_test_sequence.sh
```

## 🔧 Manual Setup (Alternative)

If you prefer to set up everything manually:

### 1. Install Prerequisites

#### Homebrew
```bash
# Install Homebrew
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# For Apple Silicon Macs, add to PATH
echo 'eval "$(/opt/homebrew/bin/brew shellenv)"' >> ~/.zprofile
eval "$(/opt/homebrew/bin/brew shellenv)"
```

#### NATS Server
```bash
# Install NATS server
brew install nats-server

# Start NATS server
nats-server --port 4222 &

# Verify it's running
lsof -i :4222
```

#### Docker (for Memgraph)
```bash
# Install Docker Desktop for Mac
# Download from: https://www.docker.com/products/docker-desktop/

# Start Memgraph
docker run -d --name memgraph -p 7687:7687 memgraph/memgraph
```

#### Python Environment
```bash
# Install Miniconda
brew install miniconda

# Create environment
conda create -n memgraph_replay python=3.10
conda activate memgraph_replay

# Install dependencies
pip install -r requirements.txt
```

### 2. Initialize USD Scene
```bash
# Initialize the USD scene structure in Memgraph
python scripts/setup/init_usd_scene.py
```

### 3. Test the Setup
```bash
# Run the test sequence
./run_test_sequence.sh
```

## 🛠️ NATS Server Management

Use the provided management script:

```bash
# Start NATS server
./scripts/tools/nats_manager.sh start

# Check status
./scripts/tools/nats_manager.sh status

# Test connection
./scripts/tools/nats_manager.sh test

# View logs
./scripts/tools/nats_manager.sh logs

# Stop NATS server
./scripts/tools/nats_manager.sh stop

# Restart NATS server
./scripts/tools/nats_manager.sh restart
```

## 🔍 Verification Steps

### 1. Check NATS Server
```bash
# Check if NATS server is running
lsof -i :4222

# Test connection
telnet localhost 4222
# Type "quit" to exit

# Or use the manager script
./scripts/tools/nats_manager.sh test
```

### 2. Check Memgraph
```bash
# Check if Memgraph is running
docker ps | grep memgraph

# Test connection (if mgclient is installed)
python -c "import mgclient; conn = mgclient.connect(host='localhost', port=7687); print('✅ Memgraph connected')"
```

### 3. Check Python Environment
```bash
# Activate environment
conda activate memgraph_replay

# Test imports
python -c "
import mgclient
import nats
import orjson
import pydantic
print('✅ All dependencies available')
"
```

## 🐛 Troubleshooting

### NATS Server Issues

**Problem**: NATS server won't start
```bash
# Check if port is already in use
lsof -i :4222

# Kill existing processes
pkill nats-server

# Try starting again
nats-server --port 4222
```

**Problem**: Connection refused
```bash
# Check if NATS server is actually running
ps aux | grep nats-server

# Check logs
./scripts/tools/nats_manager.sh logs
```

### Memgraph Issues

**Problem**: Memgraph container won't start
```bash
# Check Docker status
docker ps -a

# Remove old container
docker rm memgraph

# Start fresh
docker run -d --name memgraph -p 7687:7687 memgraph/memgraph
```

**Problem**: Can't connect to Memgraph
```bash
# Check if port is accessible
telnet localhost 7687

# Check Docker logs
docker logs memgraph
```

### Python Environment Issues

**Problem**: Module not found errors
```bash
# Ensure environment is activated
conda activate memgraph_replay

# Reinstall dependencies
pip install -r requirements.txt --force-reinstall

# Check Python path
python -c "import sys; print(sys.path)"
```

**Problem**: Import errors
```bash
# Test individual imports
python -c "import mgclient; print('mgclient OK')"
python -c "import nats; print('nats OK')"
python -c "import orjson; print('orjson OK')"
python -c "import pydantic; print('pydantic OK')"
```

### Process Management Issues

**Problem**: Processes won't stop with Ctrl+C
```bash
# Use the cleanup script
./scripts/tools/cleanup_processes.sh

# Or manually kill processes
pkill -f "memgraph_skg.py"
pkill -f "test_replay_utility.py"
pkill -f "replay_utility"
pkill nats-server
```

## 📋 System Requirements

### Hardware
- **Apple Silicon Mac**: M1, M2, M3, or newer
- **Intel Mac**: Any Intel-based Mac
- **RAM**: 4GB minimum, 8GB recommended
- **Storage**: 2GB free space

### Software
- **macOS**: 10.15 (Catalina) or newer
- **Homebrew**: Latest version
- **Docker Desktop**: Latest version
- **Python**: 3.10 or newer

### Network
- **Port 4222**: NATS server
- **Port 7687**: Memgraph database
- **Localhost access**: Required for all services

## 🎯 Success Indicators

You'll know everything is working when:

1. ✅ NATS server responds to connection tests
2. ✅ Memgraph container is running and accessible
3. ✅ Python environment has all dependencies
4. ✅ USD scene structure is initialized in Memgraph
5. ✅ Test sequence runs without errors
6. ✅ Nodes and relationships are created in Memgraph

## 📞 Getting Help

If you encounter issues:

1. **Check the logs**: Most scripts provide detailed logging
2. **Use the manager scripts**: They include status and diagnostic features
3. **Verify prerequisites**: Ensure all services are running
4. **Check the main README**: For general troubleshooting
5. **Review this guide**: For macOS-specific issues

## 🔄 Cleanup

To completely clean up the environment:

```bash
# Stop all services
./scripts/tools/cleanup_processes.sh
./scripts/tools/nats_manager.sh stop

# Remove Docker containers
docker stop memgraph
docker rm memgraph

# Remove conda environment
conda env remove -n memgraph_replay

# Remove log files
rm -rf logs/
rm -f /tmp/nats_server.log
rm -f /tmp/nats_server.pid
```

This will give you a fresh start if needed.
