#!/bin/bash

# NATS Server Setup Script for macOS (including Apple Silicon)
# This script helps set up NATS server on macOS for the memgraph replay utility

set -e

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

# Check if running on macOS
check_macos() {
    if [[ "$OSTYPE" != "darwin"* ]]; then
        log_error "This script is designed for macOS only"
        log_info "For other platforms, please refer to the NATS documentation"
        exit 1
    fi
    log_success "Detected macOS system"
}

# Check if Homebrew is installed
check_homebrew() {
    if command -v brew &> /dev/null; then
        log_success "Homebrew is already installed"
        return 0
    else
        log_warning "Homebrew not found"
        return 1
    fi
}

# Install Homebrew
install_homebrew() {
    log_info "Installing Homebrew..."
    
    # Install Homebrew
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
    
    # Add to PATH for Apple Silicon Macs
    if [[ $(uname -m) == "arm64" ]]; then
        echo 'eval "$(/opt/homebrew/bin/brew shellenv)"' >> ~/.zprofile
        eval "$(/opt/homebrew/bin/brew shellenv)"
        log_info "Added Homebrew to PATH for Apple Silicon"
    fi
    
    log_success "Homebrew installed successfully"
}

# Check if NATS server is already installed
check_nats_server() {
    if command -v nats-server &> /dev/null; then
        log_success "NATS server is already installed"
        return 0
    else
        log_warning "NATS server not found"
        return 1
    fi
}

# Install NATS server
install_nats_server() {
    log_info "Installing NATS server via Homebrew..."
    brew install nats-server
    log_success "NATS server installed successfully"
}

# Check if NATS server is already running
check_nats_running() {
    if lsof -i :4222 &> /dev/null; then
        log_success "NATS server is already running on port 4222"
        return 0
    else
        log_warning "NATS server is not running"
        return 1
    fi
}

# Start NATS server
start_nats_server() {
    log_info "Starting NATS server on localhost:4222..."
    
    # Start NATS server in background
    nats-server --port 4222 &
    local nats_pid=$!
    
    # Wait a moment for server to start
    sleep 2
    
    # Check if it's running
    if lsof -i :4222 &> /dev/null; then
        log_success "NATS server started successfully (PID: $nats_pid)"
        echo "PID: $nats_pid" > /tmp/nats_server.pid
        return 0
    else
        log_error "Failed to start NATS server"
        return 1
    fi
}

# Test NATS connection
test_nats_connection() {
    log_info "Testing NATS server connection..."
    
    # Try to connect using telnet
    if echo "quit" | timeout 5 telnet localhost 4222 &> /dev/null; then
        log_success "NATS server connection test passed"
        return 0
    else
        log_error "NATS server connection test failed"
        return 1
    fi
}

# Show status
show_status() {
    log_info "NATS Server Status:"
    echo "==================="
    
    if command -v nats-server &> /dev/null; then
        echo "✅ NATS server is installed"
        nats-server --version
    else
        echo "❌ NATS server is not installed"
    fi
    
    if lsof -i :4222 &> /dev/null; then
        echo "✅ NATS server is running on port 4222"
        lsof -i :4222
    else
        echo "❌ NATS server is not running"
    fi
    
    echo ""
    log_info "To start NATS server manually:"
    echo "  nats-server --port 4222"
    echo ""
    log_info "To stop NATS server:"
    echo "  pkill nats-server"
    echo "  # Or if you have the PID file:"
    echo "  kill \$(cat /tmp/nats_server.pid)"
}

# Main function
main() {
    log_info "NATS Server Setup for macOS"
    log_info "============================"
    
    # Check if running on macOS
    check_macos
    
    # Check/install Homebrew
    if ! check_homebrew; then
        install_homebrew
    fi
    
    # Check/install NATS server
    if ! check_nats_server; then
        install_nats_server
    fi
    
    # Check if NATS server is running
    if ! check_nats_running; then
        if start_nats_server; then
            # Test connection
            if test_nats_connection; then
                log_success "NATS server setup completed successfully!"
            else
                log_error "NATS server started but connection test failed"
                exit 1
            fi
        else
            log_error "Failed to start NATS server"
            exit 1
        fi
    else
        log_success "NATS server is already running"
        if test_nats_connection; then
            log_success "NATS server connection test passed"
        else
            log_warning "NATS server is running but connection test failed"
        fi
    fi
    
    # Show final status
    echo ""
    show_status
    
    echo ""
    log_success "Setup complete! You can now run the memgraph replay utility."
    log_info "Next steps:"
    echo "  1. Start Memgraph: docker run -p 7687:7687 memgraph/memgraph"
    echo "  2. Setup conda environment: ./setup_conda_env.sh"
    echo "  3. Run test sequence: ./run_test_sequence.sh"
}

# Run main function
main "$@"
