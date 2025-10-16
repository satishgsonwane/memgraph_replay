# NATS-Memgraph Replay Utility - Apple Silicon Setup

This project is **fully compatible with Apple Silicon Macs** (M1, M2, M3). The setup has been optimized to work seamlessly on ARM64 architecture.

## 🍎 Apple Silicon Compatibility

### ✅ **Fully Compatible Components:**

- **Python 3.10+** - Native ARM64 support via Conda
- **NATS Server** - Official ARM64 binaries available
- **orjson** - Latest versions have Apple Silicon fixes
- **pydantic** - Compatible with ARM64 (use latest versions)
- **tenacity** - Pure Python, architecture-independent
- **filterpy** - Pure Python, architecture-independent
- **numpy/pandas** - Native ARM64 support via Conda
- **psutil** - Cross-platform, ARM64 compatible
- **pymgclient** - Compiles natively on Apple Silicon

### 🔧 **Installation Methods:**

#### Method 1: Apple Silicon Optimized Setup (Recommended)
```bash
# Use the Apple Silicon optimized setup script
./setup_apple_silicon.sh
```

#### Method 2: Manual Setup
```bash
# Create conda environment
conda create -n memgraph_replay python=3.10 -y
conda activate memgraph_replay

# Install NATS server (ARM64 binary)
curl -L https://github.com/nats-io/nats-server/releases/latest/download/nats-server-darwin-arm64.zip -o nats-server.zip
unzip nats-server.zip
sudo mv nats-server /usr/local/bin/
sudo chmod +x /usr/local/bin/nats-server

# Install Python packages
pip install --upgrade pip setuptools wheel
pip install orjson pydantic tenacity nats-py filterpy psutil numpy pandas
pip install pymgclient  # This will compile natively for ARM64
```

#### Method 3: Using Conda Environment File
```bash
# Use the Apple Silicon optimized environment file
conda env create -f environment_apple_silicon.yml
conda activate memgraph_replay
```

## 🚀 **Quick Start:**

1. **Clone and setup:**
   ```bash
   git clone <your-repo>
   cd memgraph_replay
   ./setup_apple_silicon.sh
   ```

2. **Activate environment:**
   ```bash
   ./activate_env.sh
   # OR
   conda activate memgraph_replay
   ```

3. **Test installation:**
   ```bash
   python test_environment.py
   ```

4. **Start NATS server:**
   ```bash
   nats-server --port 4222 --http_port 8222
   ```

## 🔍 **Troubleshooting Apple Silicon Issues:**

### Common Issues and Solutions:

1. **pymgclient compilation fails:**
   ```bash
   # Install build dependencies
   brew install cmake openssl
   export LDFLAGS="-L$(brew --prefix openssl)/lib"
   export CPPFLAGS="-I$(brew --prefix openssl)/include"
   pip install pymgclient
   ```

2. **orjson installation issues:**
   ```bash
   # Use latest version
   pip install --upgrade orjson
   ```

3. **pydantic-core compilation issues:**
   ```bash
   # Install pre-compiled wheels
   pip install --upgrade pydantic pydantic-core
   ```

4. **NATS server not found:**
   ```bash
   # Download ARM64 binary manually
   curl -L https://github.com/nats-io/nats-server/releases/latest/download/nats-server-darwin-arm64.zip -o nats-server.zip
   unzip nats-server.zip
   sudo mv nats-server /usr/local/bin/
   ```

### Performance Notes:

- **Native ARM64 binaries** provide optimal performance
- **Conda packages** are pre-compiled for ARM64
- **pip packages** compile natively on Apple Silicon
- **Memory usage** is optimized for ARM64 architecture

## 📊 **Architecture Detection:**

The setup script automatically detects your architecture:

- **Apple Silicon (ARM64)**: `darwin-arm64`
- **Intel Mac (x86_64)**: `darwin-amd64`
- **Linux ARM64**: `linux-arm64`
- **Linux x86_64**: `linux-amd64`

## 🧪 **Testing:**

Run the comprehensive test suite:
```bash
python test_environment.py
```

Expected output on Apple Silicon:
```
🖥️ System Information:
  Platform: macOS-13.0-arm64-arm-64bit
  Architecture: arm64
  Python: 3.10.18
  ✅ Apple Silicon Mac detected

📦 Testing Python package imports...
✅ mgclient (Memgraph client): Available
✅ nats (NATS client): Available
✅ orjson (Fast JSON library): 3.11.3
✅ pydantic (Data validation): 2.12.2
✅ tenacity (Retry library): Available
✅ filterpy (Signal processing): 1.4.5
✅ numpy (Numerical computing): 2.2.6
✅ pandas (Data manipulation): 2.3.3
✅ psutil (System utilities): 7.1.0

🚀 Testing NATS server...
✅ NATS server: nats-server: v2.10.12
```

## 🔗 **Useful Links:**

- [NATS Server ARM64 Releases](https://github.com/nats-io/nats-server/releases)
- [Conda Apple Silicon Support](https://docs.conda.io/en/latest/miniconda.html#macos-installers)
- [Python ARM64 Support](https://www.python.org/downloads/macos/)
- [Homebrew Apple Silicon](https://brew.sh/)

## 📝 **Notes:**

- All packages are tested on Apple Silicon Macs
- Setup scripts automatically handle architecture detection
- Native ARM64 binaries provide best performance
- Compilation issues are handled with proper build dependencies
- Environment is fully isolated and reproducible

Your Apple Silicon Mac is ready to run the NATS-Memgraph Replay Utility! 🎉
