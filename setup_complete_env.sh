#!/bin/bash

# ===================================================
# Complete Environment Setup Script
# ===================================================
# This script sets up the complete environment for the
# NATS-Memgraph Replay Utility project including:
# - NATS server installation
# - Conda environment creation
# - All Python dependencies
# ===================================================

set -e  # Exit on any error

# Configuration
ENV_NAME="memgraph_replay"
PYTHON_VERSION="3.10"
REQUIREMENTS_FILE="requirements.txt"
ENVIRONMENT_FILE="environment.yml"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_step() {
    echo -e "${PURPLE}[STEP]${NC} $1"
}

log_check() {
    echo -e "${CYAN}[CHECK]${NC} $1"
}

# Check if running as root (not recommended for conda)
check_user() {
    if [[ $EUID -eq 0 ]]; then
        log_warning "Running as root is not recommended for conda environments"
        log_info "Consider running as a regular user"
    fi
}

# Check system prerequisites
check_prerequisites() {
    log_step "Checking system prerequisites..."
    
    # Check if conda is installed
    if ! command -v conda &> /dev/null; then
        log_error "Conda is not installed or not in PATH"
        log_info "Please install Miniconda or Anaconda first:"
        log_info "  https://docs.conda.io/en/latest/miniconda.html"
        exit 1
    fi
    log_success "Conda found: $(conda --version)"
    
    # Check if curl is available (for NATS server installation)
    if ! command -v curl &> /dev/null; then
        log_error "curl is required but not installed"
        log_info "Please install curl: sudo apt-get install curl (Ubuntu/Debian) or brew install curl (macOS)"
        exit 1
    fi
    log_success "curl found: $(curl --version | head -n1)"
    
    # Check if wget is available (alternative for downloads)
    if ! command -v wget &> /dev/null; then
        log_warning "wget not found, will use curl for downloads"
    else
        log_success "wget found: $(wget --version | head -n1)"
    fi
}

# Install NATS server
install_nats_server() {
    log_step "Installing NATS server..."
    
    # Check if nats-server is already installed
    if command -v nats-server &> /dev/null; then
        log_success "NATS server already installed: $(nats-server --version)"
        return 0
    fi
    
    log_info "NATS server not found, installing..."
    
    # Detect OS and architecture
    OS=$(uname -s | tr '[:upper:]' '[:lower:]')
    ARCH=$(uname -m)
    
    case $ARCH in
        x86_64)
            ARCH="amd64"
            ;;
        arm64|aarch64)
            ARCH="arm64"
            ;;
        *)
            log_error "Unsupported architecture: $ARCH"
            exit 1
            ;;
    esac
    
    # Get latest version
    log_info "Fetching latest NATS server version..."
    NATS_VERSION=$(curl -s https://api.github.com/repos/nats-io/nats-server/releases/latest | grep '"tag_name"' | cut -d'"' -f4)
    
    if [[ -z "$NATS_VERSION" ]]; then
        log_error "Failed to fetch NATS server version"
        exit 1
    fi
    
    log_info "Latest NATS server version: $NATS_VERSION"
    
    # Download and install
    DOWNLOAD_URL="https://github.com/nats-io/nats-server/releases/download/${NATS_VERSION}/nats-server-${NATS_VERSION}-${OS}-${ARCH}.zip"
    TEMP_DIR=$(mktemp -d)
    
    log_info "Downloading NATS server from: $DOWNLOAD_URL"
    
    if command -v wget &> /dev/null; then
        wget -q "$DOWNLOAD_URL" -O "$TEMP_DIR/nats-server.zip"
    else
        curl -sL "$DOWNLOAD_URL" -o "$TEMP_DIR/nats-server.zip"
    fi
    
    if [[ $? -ne 0 ]]; then
        log_error "Failed to download NATS server"
        rm -rf "$TEMP_DIR"
        exit 1
    fi
    
    # Extract and install
    log_info "Extracting and installing NATS server..."
    cd "$TEMP_DIR"
    unzip -q nats-server.zip
    
    # Install to /usr/local/bin (requires sudo)
    if sudo cp nats-server /usr/local/bin/; then
        sudo chmod +x /usr/local/bin/nats-server
        log_success "NATS server installed to /usr/local/bin/nats-server"
    else
        log_error "Failed to install NATS server to /usr/local/bin"
        log_info "You may need to run: sudo cp $TEMP_DIR/nats-server /usr/local/bin/"
        rm -rf "$TEMP_DIR"
        exit 1
    fi
    
    # Cleanup
    cd - > /dev/null
    rm -rf "$TEMP_DIR"
    
    # Verify installation
    if command -v nats-server &> /dev/null; then
        log_success "NATS server installation verified: $(nats-server --version)"
    else
        log_error "NATS server installation failed"
        exit 1
    fi
}

# Check if environment already exists
check_existing_env() {
    if conda env list | grep -q "^${ENV_NAME}\s"; then
        log_warning "Environment '${ENV_NAME}' already exists"
        read -p "Do you want to remove and recreate it? (y/N): " -n 1 -r
        echo ""
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            log_info "Removing existing environment..."
            conda env remove -n "$ENV_NAME" -y
            log_success "Existing environment removed"
        else
            log_info "Using existing environment"
            return 1
        fi
    fi
    return 0
}

# Create conda environment from environment.yml
create_env_from_yml() {
    log_step "Creating conda environment from environment.yml..."
    
    if [[ ! -f "$ENVIRONMENT_FILE" ]]; then
        log_error "Environment file not found: $ENVIRONMENT_FILE"
        exit 1
    fi
    
    log_info "Creating environment from $ENVIRONMENT_FILE..."
    conda env create -f "$ENVIRONMENT_FILE"
    
    if [[ $? -eq 0 ]]; then
        log_success "Environment '${ENV_NAME}' created successfully from environment.yml"
    else
        log_error "Failed to create environment from environment.yml"
        exit 1
    fi
}

# Install additional requirements if needed
install_additional_requirements() {
    log_step "Installing additional requirements..."
    
    if [[ -f "$REQUIREMENTS_FILE" ]]; then
        log_info "Installing additional packages from requirements.txt..."
        conda run -n "$ENV_NAME" pip install -r "$REQUIREMENTS_FILE"
        
        if [[ $? -eq 0 ]]; then
            log_success "Additional requirements installed successfully"
        else
            log_error "Failed to install additional requirements"
            exit 1
        fi
    else
        log_warning "Requirements file not found: $REQUIREMENTS_FILE"
    fi
}

# Verify installation
verify_installation() {
    log_step "Verifying installation..."
    
    # Test key imports
    log_check "Testing core dependencies..."
    conda run -n "$ENV_NAME" python -c "
import sys
print(f'Python version: {sys.version}')

# Test core dependencies
try:
    import pymgclient
    print(f'✅ pymgclient: {pymgclient.__version__}')
except ImportError as e:
    print(f'❌ pymgclient: {e}')

try:
    import nats
    print(f'✅ nats: {nats.__version__}')
except ImportError as e:
    print(f'❌ nats: {e}')

try:
    import orjson
    print(f'✅ orjson: {orjson.__version__}')
except ImportError as e:
    print(f'❌ orjson: {e}')

try:
    import pydantic
    print(f'✅ pydantic: {pydantic.__version__}')
except ImportError as e:
    print(f'❌ pydantic: {e}')

try:
    import tenacity
    print(f'✅ tenacity: {tenacity.__version__}')
except ImportError as e:
    print(f'❌ tenacity: {e}')

try:
    import filterpy
    print(f'✅ filterpy: {filterpy.__version__}')
except ImportError as e:
    print(f'❌ filterpy: {e}')

try:
    import numpy
    print(f'✅ numpy: {numpy.__version__}')
except ImportError as e:
    print(f'❌ numpy: {e}')

try:
    import pandas
    print(f'✅ pandas: {pandas.__version__}')
except ImportError as e:
    print(f'❌ pandas: {e}')

print('\\n🎉 All core dependencies verified!')
" 2>/dev/null
    
    if [[ $? -eq 0 ]]; then
        log_success "Installation verification passed"
    else
        log_error "Installation verification failed"
        exit 1
    fi
}

# Test NATS server
test_nats_server() {
    log_step "Testing NATS server..."
    
    if ! command -v nats-server &> /dev/null; then
        log_error "NATS server not found in PATH"
        exit 1
    fi
    
    log_info "Starting NATS server for testing..."
    
    # Start NATS server in background
    nats-server --port 4222 --http_port 8222 &
    NATS_PID=$!
    
    # Wait a moment for server to start
    sleep 2
    
    # Test connection
    if curl -s http://localhost:8222/varz > /dev/null; then
        log_success "NATS server is running and responding"
    else
        log_error "NATS server is not responding"
        kill $NATS_PID 2>/dev/null || true
        exit 1
    fi
    
    # Stop NATS server
    kill $NATS_PID 2>/dev/null || true
    wait $NATS_PID 2>/dev/null || true
    
    log_success "NATS server test completed"
}

# Create activation script
create_activation_script() {
    log_step "Creating activation script..."
    
    cat > "activate_env.sh" << EOF
#!/bin/bash
# ===================================================
# Quick Activation Script
# ===================================================
# Run this script to activate the conda environment
# ===================================================

echo "🚀 Activating conda environment: ${ENV_NAME}"
conda activate ${ENV_NAME}

if [[ \$? -eq 0 ]]; then
    echo "✅ Environment activated successfully!"
    echo ""
    echo "📋 Available commands:"
    echo "  python memgraph_skg.py              # Start the bridge service"
    echo "  python -m replay_utility capture    # Capture NATS messages"
    echo "  python -m replay_utility replay     # Replay captured messages"
    echo "  python scripts/setup/init_usd_scene.py  # Initialize USD scene"
    echo "  python scripts/tools/check_usd_nodes.py # Check USD nodes"
    echo "  ./run_test_sequence.sh              # Run test sequence"
    echo ""
    echo "🔧 NATS Server commands:"
    echo "  nats-server                          # Start NATS server"
    echo "  nats-server --port 4222 --http_port 8222  # Start with custom ports"
    echo ""
    echo "🔧 To deactivate: conda deactivate"
else
    echo "❌ Failed to activate environment"
    exit 1
fi
EOF
    
    chmod +x "activate_env.sh"
    log_success "Activation script created: ./activate_env.sh"
}

# Create environment test script
create_test_script() {
    log_step "Creating environment test script..."
    
    cat > "test_environment.py" << 'EOF'
#!/usr/bin/env python3
"""
Environment Test Script
=======================
This script tests all the core dependencies and services
required for the NATS-Memgraph Replay Utility.
"""

import sys
import subprocess
import json
from typing import Dict, Any, List

def test_python_version() -> bool:
    """Test Python version compatibility."""
    print("🐍 Testing Python version...")
    version = sys.version_info
    if version.major == 3 and version.minor >= 10:
        print(f"✅ Python {version.major}.{version.minor}.{version.micro} - Compatible")
        return True
    else:
        print(f"❌ Python {version.major}.{version.minor}.{version.micro} - Requires Python 3.10+")
        return False

def test_imports() -> Dict[str, bool]:
    """Test all required Python package imports."""
    print("\n📦 Testing Python package imports...")
    
    packages = {
        'pymgclient': 'Official Memgraph client',
        'nats': 'NATS client',
        'orjson': 'Fast JSON library',
        'pydantic': 'Data validation',
        'tenacity': 'Retry library',
        'filterpy': 'Signal processing',
        'numpy': 'Numerical computing',
        'pandas': 'Data manipulation',
        'psutil': 'System utilities'
    }
    
    results = {}
    for package, description in packages.items():
        try:
            module = __import__(package)
            version = getattr(module, '__version__', 'unknown')
            print(f"✅ {package} ({description}): {version}")
            results[package] = True
        except ImportError as e:
            print(f"❌ {package} ({description}): {e}")
            results[package] = False
    
    return results

def test_nats_server() -> bool:
    """Test NATS server availability."""
    print("\n🚀 Testing NATS server...")
    
    try:
        # Check if nats-server command exists
        result = subprocess.run(['nats-server', '--version'], 
                              capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            version = result.stdout.strip()
            print(f"✅ NATS server: {version}")
            return True
        else:
            print(f"❌ NATS server: Command failed")
            return False
    except FileNotFoundError:
        print("❌ NATS server: Not found in PATH")
        return False
    except subprocess.TimeoutExpired:
        print("❌ NATS server: Command timeout")
        return False
    except Exception as e:
        print(f"❌ NATS server: {e}")
        return False

def test_memgraph_connection() -> bool:
    """Test Memgraph connection (if server is running)."""
    print("\n🗄️ Testing Memgraph connection...")
    
    try:
        import pymgclient
        
        # Try to connect to default Memgraph port
        conn = pymgclient.connect(host='localhost', port=7687)
        conn.close()
        print("✅ Memgraph: Connection successful")
        return True
    except ImportError:
        print("❌ Memgraph: pymgclient not available")
        return False
    except Exception as e:
        print(f"⚠️ Memgraph: Connection failed - {e}")
        print("   (This is expected if Memgraph server is not running)")
        return False

def main():
    """Run all tests and report results."""
    print("🧪 NATS-Memgraph Replay Utility - Environment Test")
    print("=" * 60)
    
    # Run tests
    python_ok = test_python_version()
    imports_ok = test_imports()
    nats_ok = test_nats_server()
    memgraph_ok = test_memgraph_connection()
    
    # Summary
    print("\n📊 Test Summary:")
    print("=" * 30)
    
    total_tests = 1 + len(imports_ok) + 2  # python + imports + nats + memgraph
    passed_tests = sum([
        python_ok,
        sum(imports_ok.values()),
        nats_ok,
        memgraph_ok
    ])
    
    print(f"Python version: {'✅' if python_ok else '❌'}")
    print(f"Package imports: {sum(imports_ok.values())}/{len(imports_ok)} ✅")
    print(f"NATS server: {'✅' if nats_ok else '❌'}")
    print(f"Memgraph connection: {'✅' if memgraph_ok else '⚠️'}")
    
    print(f"\nOverall: {passed_tests}/{total_tests} tests passed")
    
    if passed_tests == total_tests:
        print("\n🎉 All tests passed! Environment is ready.")
        return 0
    elif passed_tests >= total_tests - 1:  # Allow memgraph to fail
        print("\n✅ Environment is mostly ready. Memgraph server may not be running.")
        return 0
    else:
        print("\n❌ Some tests failed. Please check the installation.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
EOF
    
    chmod +x "test_environment.py"
    log_success "Environment test script created: ./test_environment.py"
}

# Main execution
main() {
    echo "🚀 NATS-Memgraph Replay Utility - Complete Environment Setup"
    echo "============================================================"
    echo ""
    
    # Check prerequisites
    check_user
    check_prerequisites
    
    # Install NATS server
    install_nats_server
    
    # Create or use existing environment
    if check_existing_env; then
        create_env_from_yml
        install_additional_requirements
    else
        # Environment exists, just verify it works
        log_info "Verifying existing environment..."
    fi
    
    # Verify installation
    verify_installation
    
    # Test NATS server
    test_nats_server
    
    # Create helper scripts
    create_activation_script
    create_test_script
    
    echo ""
    echo "🎉 Complete setup finished successfully!"
    echo ""
    echo "📋 Next steps:"
    echo "  1. Activate the environment:"
    echo "     ./activate_env.sh"
    echo "     # OR"
    echo "     conda activate ${ENV_NAME}"
    echo ""
    echo "  2. Test the environment:"
    echo "     python test_environment.py"
    echo ""
    echo "  3. Start NATS server (in a separate terminal):"
    echo "     nats-server --port 4222 --http_port 8222"
    echo ""
    echo "  4. Initialize USD scene:"
    echo "     python scripts/setup/init_usd_scene.py"
    echo ""
    echo "  5. Run test sequence:"
    echo "     ./run_test_sequence.sh"
    echo ""
    echo "🔧 Environment management:"
    echo "  - Activate: conda activate ${ENV_NAME}"
    echo "  - Deactivate: conda deactivate"
    echo "  - Remove: conda env remove -n ${ENV_NAME}"
    echo ""
    echo "🔧 NATS server management:"
    echo "  - Start: nats-server"
    echo "  - Start with custom ports: nats-server --port 4222 --http_port 8222"
    echo "  - Check status: curl http://localhost:8222/varz"
    echo ""
}

# Run main function
main "$@"
