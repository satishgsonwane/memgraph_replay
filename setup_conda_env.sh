#!/bin/bash

# ===================================================
# Conda Environment Setup Script
# ===================================================
# This script creates and activates a conda environment
# for the NATS-Memgraph Replay Utility project
# ===================================================

set -e  # Exit on any error

# Configuration
ENV_NAME="memgraph_replay"
PYTHON_VERSION="3.10"
REQUIREMENTS_FILE="requirements.txt"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
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

# Check if conda is installed
check_conda() {
    if ! command -v conda &> /dev/null; then
        log_error "Conda is not installed or not in PATH"
        log_info "Please install Miniconda or Anaconda first:"
        log_info "  https://docs.conda.io/en/latest/miniconda.html"
        exit 1
    fi
    log_success "Conda found: $(conda --version)"
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

# Create conda environment
create_env() {
    log_info "Creating conda environment '${ENV_NAME}' with Python ${PYTHON_VERSION}..."
    
    conda create -n "$ENV_NAME" python="$PYTHON_VERSION" -y
    
    if [[ $? -eq 0 ]]; then
        log_success "Environment '${ENV_NAME}' created successfully"
    else
        log_error "Failed to create environment"
        exit 1
    fi
}

# Install requirements
install_requirements() {
    log_info "Installing Python packages from requirements.txt..."
    
    if [[ ! -f "$REQUIREMENTS_FILE" ]]; then
        log_error "Requirements file not found: $REQUIREMENTS_FILE"
        exit 1
    fi
    
    # Activate environment and install packages
    conda run -n "$ENV_NAME" pip install -r "$REQUIREMENTS_FILE"
    
    if [[ $? -eq 0 ]]; then
        log_success "Requirements installed successfully"
    else
        log_error "Failed to install requirements"
        exit 1
    fi
}

# Verify installation
verify_installation() {
    log_info "Verifying installation..."
    
    # Test key imports
    conda run -n "$ENV_NAME" python -c "
import mgclient
import nats
import orjson
import pydantic
print('✅ All core dependencies imported successfully')
print(f'  mgclient: {mgclient.__version__}')
print(f'  nats: {nats.__version__}')
print(f'  orjson: {orjson.__version__}')
print(f'  pydantic: {pydantic.__version__}')
" 2>/dev/null
    
    if [[ $? -eq 0 ]]; then
        log_success "Installation verification passed"
    else
        log_error "Installation verification failed"
        exit 1
    fi
}

# Create activation script
create_activation_script() {
    log_info "Creating activation script..."
    
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
    echo "🔧 To deactivate: conda deactivate"
else
    echo "❌ Failed to activate environment"
    exit 1
fi
EOF
    
    chmod +x "activate_env.sh"
    log_success "Activation script created: ./activate_env.sh"
}

# Main execution
main() {
    echo "🐍 NATS-Memgraph Replay Utility - Conda Environment Setup"
    echo "=========================================================="
    echo ""
    
    # Check prerequisites
    check_conda
    
    # Create or use existing environment
    if check_existing_env; then
        create_env
        install_requirements
        verify_installation
    else
        # Environment exists, just verify it works
        log_info "Verifying existing environment..."
        verify_installation
    fi
    
    # Create activation script
    create_activation_script
    
    echo ""
    echo "🎉 Setup completed successfully!"
    echo ""
    echo "📋 Next steps:"
    echo "  1. Activate the environment:"
    echo "     ./activate_env.sh"
    echo "     # OR"
    echo "     conda activate ${ENV_NAME}"
    echo ""
    echo "  2. Test environment:"
    echo "     python test_environment.py"
    echo ""
    echo "  3. Initialize USD scene:"
    echo "     python scripts/setup/init_usd_scene.py"
    echo ""
    echo "  4. Run test sequence:"
    echo "     ./run_test_sequence.sh"
    echo ""
    echo "🔧 Environment management:"
    echo "  - Activate: conda activate ${ENV_NAME}"
    echo "  - Deactivate: conda deactivate"
    echo "  - Remove: conda env remove -n ${ENV_NAME}"
    echo ""
}

# Run main function
main "$@"
