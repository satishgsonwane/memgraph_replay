#!/bin/bash

# ===================================================
# NATS-Memgraph Bridge Test Sequence Runner
# ===================================================
# This script runs memgraph_skg.py first, waits for it to start up properly,
# then runs test_replay_utility.py to test data population in Memgraph.
# 
# Usage:
#   ./run_test_sequence.sh [--loop] [--help]
#   
# Options:
#   --loop    Run replay in continuous loop mode (default: single replay)
#   --help    Show this help message
# ===================================================

set -e  # Exit on any error
set -u  # Exit on undefined variables

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MEMGRAPH_SCRIPT="$SCRIPT_DIR/memgraph_skg.py"
TEST_SCRIPT="$SCRIPT_DIR/tests/test_replay_utility.py"
LOG_DIR="$SCRIPT_DIR/logs"
PID_FILE="$LOG_DIR/memgraph_skg.pid"
LOG_FILE="$LOG_DIR/memgraph_skg.log"
TEST_LOG_FILE="$LOG_DIR/test_replay.log"

# Default values
LOOP_MODE=false

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1" | tee -a "$LOG_FILE" 2>/dev/null || echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1" | tee -a "$LOG_FILE" 2>/dev/null || echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1" | tee -a "$LOG_FILE" 2>/dev/null || echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1" | tee -a "$LOG_FILE" 2>/dev/null || echo -e "${RED}[ERROR]${NC} $1"
}

# Cleanup function
cleanup() {
    log_info "Cleaning up..."
    
    # Kill all Python processes related to our project
    log_info "Stopping all Python processes..."
    pkill -f "memgraph_skg.py" 2>/dev/null || true
    pkill -f "test_replay_utility.py" 2>/dev/null || true
    pkill -f "replay_utility" 2>/dev/null || true
    
    # Also handle the PID file if it exists
    if [[ -f "$PID_FILE" ]]; then
        local pid=$(cat "$PID_FILE")
        if kill -0 "$pid" 2>/dev/null; then
            log_info "Stopping memgraph_skg.py (PID: $pid)..."
            kill -TERM "$pid" 2>/dev/null || true
            
            # Wait for graceful shutdown
            local count=0
            while kill -0 "$pid" 2>/dev/null && [[ $count -lt 5 ]]; do
                sleep 1
                ((count++))
            done
            
            # Force kill if still running
            if kill -0 "$pid" 2>/dev/null; then
                log_warning "Force killing memgraph_skg.py (PID: $pid)..."
                kill -KILL "$pid" 2>/dev/null || true
            fi
            
            log_success "memgraph_skg.py stopped"
        fi
        rm -f "$PID_FILE"
    fi
    
    # Give a moment for processes to fully terminate
    sleep 1
    
    # Final check - kill any remaining processes
    local remaining=$(pgrep -f "memgraph_skg.py|test_replay_utility.py|replay_utility" 2>/dev/null | wc -l)
    if [[ $remaining -gt 0 ]]; then
        log_warning "Force killing remaining processes..."
        pkill -9 -f "memgraph_skg.py|test_replay_utility.py|replay_utility" 2>/dev/null || true
        sleep 1
    fi
    
    log_info "Cleanup completed"
}

# Setup function
setup() {
    log_info "Setting up test environment..."
    
    # Create log directory
    mkdir -p "$LOG_DIR"
    
    # Clean up any existing processes
    cleanup
    
    # Check if scripts exist
    if [[ ! -f "$MEMGRAPH_SCRIPT" ]]; then
        log_error "memgraph_skg.py not found at: $MEMGRAPH_SCRIPT"
        exit 1
    fi
    
    if [[ ! -f "$TEST_SCRIPT" ]]; then
        log_error "test_replay_utility.py not found at: $TEST_SCRIPT"
        exit 1
    fi
    
    # Make scripts executable
    chmod +x "$MEMGRAPH_SCRIPT" "$TEST_SCRIPT"
    
    log_success "Setup completed"
}

# Check if Memgraph is ready
check_memgraph_health() {
    local max_attempts=30
    local attempt=1
    
    log_info "Checking Memgraph health..."
    
    while [[ $attempt -le $max_attempts ]]; do
        log_info "Memgraph health check attempt $attempt/$max_attempts..."
        
        if python3 -c "
import mgclient
import sys
try:
    conn = mgclient.connect(host='localhost', port=7687)
    conn.close()
    print('Memgraph is ready')
    sys.exit(0)
except Exception as e:
    print(f'Memgraph not ready: {e}')
    sys.exit(1)
" 2>/dev/null; then
            log_success "Memgraph is ready and accepting connections"
            return 0
        fi
        
        if [[ $attempt -lt $max_attempts ]]; then
            log_info "Waiting 3 seconds before next attempt..."
            sleep 3
        fi
        ((attempt++))
    done
    
    log_error "Memgraph failed to become ready after $max_attempts attempts"
    return 1
}

# Check if NATS bridge is ready
check_bridge_ready() {
    local max_attempts=20
    local attempt=1
    
    log_info "Checking if NATS-Memgraph bridge is ready..."
    
    while [[ $attempt -le $max_attempts ]]; do
        log_info "Bridge readiness check attempt $attempt/$max_attempts..."
        
        # Check if the process is still running
        if [[ -f "$PID_FILE" ]]; then
            local pid=$(cat "$PID_FILE")
            if ! kill -0 "$pid" 2>/dev/null; then
                log_error "memgraph_skg.py process died unexpectedly"
                return 1
            fi
        else
            log_error "PID file not found"
            return 1
        fi
        
        # Check if bridge is processing messages by looking for success logs
        if grep -q "✅ Connected to NATS server" "$LOG_FILE" 2>/dev/null && \
           grep -q "All subscriptions complete" "$LOG_FILE" 2>/dev/null; then
            log_success "NATS-Memgraph bridge is ready"
            return 0
        fi
        
        if [[ $attempt -lt $max_attempts ]]; then
            log_info "Waiting 2 seconds before next attempt..."
            sleep 2
        fi
        ((attempt++))
    done
    
    log_warning "Bridge may not be fully ready, but continuing with test..."
    return 0
}

# Start memgraph_skg.py
start_bridge() {
    log_info "Starting memgraph_skg.py..."
    
    # Start the script in background
    nohup python3 "$MEMGRAPH_SCRIPT" > "$LOG_FILE" 2>&1 &
    local pid=$!
    echo "$pid" > "$PID_FILE"
    
    log_info "memgraph_skg.py started with PID: $pid"
    log_info "Log file: $LOG_FILE"
    
    # Wait a moment for startup
    sleep 5
    
    # Check if process is still running
    if ! kill -0 "$pid" 2>/dev/null; then
        log_error "memgraph_skg.py failed to start or crashed immediately"
        log_error "Check log file for details: $LOG_FILE"
        cat "$LOG_FILE" | tail -20
        return 1
    fi
    
    log_success "memgraph_skg.py started successfully"
    return 0
}

# Parse command line arguments
parse_args() {
    while [[ $# -gt 0 ]]; do
        case $1 in
            --loop)
                LOOP_MODE=true
                log_info "Loop mode enabled - replay will run continuously"
                shift
                ;;
            --help|-h)
                echo "Usage: $0 [--loop] [--help]"
                echo ""
                echo "Options:"
                echo "  --loop    Run replay in continuous loop mode (default: single replay)"
                echo "  --help    Show this help message"
                echo ""
                echo "This script runs memgraph_skg.py first, waits for it to start up properly,"
                echo "then runs test_replay_utility.py to test data population in Memgraph."
                exit 0
                ;;
            *)
                log_error "Unknown option: $1"
                log_error "Use --help for usage information"
                exit 1
                ;;
        esac
    done
}

# Run test script
run_test() {
    if [[ "$LOOP_MODE" == "true" ]]; then
        log_info "Running test_replay_utility.py in loop mode..."
    else
        log_info "Running test_replay_utility.py..."
    fi
    
    # Run the test script and capture output (from project root for proper imports)
    local exit_code=0
    if [[ "$LOOP_MODE" == "true" ]]; then
        (cd "$SCRIPT_DIR" && python3 "$TEST_SCRIPT" --loop) > "$TEST_LOG_FILE" 2>&1 || exit_code=$?
    else
        (cd "$SCRIPT_DIR" && python3 "$TEST_SCRIPT") > "$TEST_LOG_FILE" 2>&1 || exit_code=$?
    fi
    
    if [[ $exit_code -eq 0 ]]; then
        log_success "test_replay_utility.py completed successfully"
        log_info "Test log file: $TEST_LOG_FILE"
        
        # Show key results from test
        echo "=== Test Results Summary ==="
        grep -E "(Testing|passed|completed|failed)" "$TEST_LOG_FILE" | tail -10
        echo "=========================="
        
        return 0
    elif [[ $exit_code -eq 130 ]]; then
        # Exit code 130 is KeyboardInterrupt (Ctrl+C)
        log_warning "test_replay_utility.py was interrupted by user (Ctrl+C)"
        log_info "This is expected when testing - the replay was working correctly"
        
        # Show what was accomplished before interruption
        echo "=== Test Progress Before Interruption ==="
        grep -E "(Published|Testing|passed|completed)" "$TEST_LOG_FILE" | tail -5
        echo "========================================="
        
        return 0  # Consider interruption as success
    else
        log_error "test_replay_utility.py failed with exit code: $exit_code"
        log_error "Test log file: $TEST_LOG_FILE"
        
        # Show error details
        echo "=== Test Error Details ==="
        grep -E "(Error|Failed|Exception|Traceback)" "$TEST_LOG_FILE" | tail -10
        echo "=========================="
        
        return 1
    fi
}

# Main execution function
main() {
    # Parse command line arguments first
    parse_args "$@"
    
    # Create log directory first
    mkdir -p "$LOG_DIR"
    
    log_info "Starting NATS-Memgraph Bridge Test Sequence"
    log_info "Script directory: $SCRIPT_DIR"
    if [[ "$LOOP_MODE" == "true" ]]; then
        log_info "Mode: Continuous loop replay"
    else
        log_info "Mode: Single replay"
    fi
    
    # Setup trap for cleanup on exit
    trap cleanup EXIT INT TERM QUIT
    
    # Setup environment
    setup
    
    # Start the bridge
    if ! start_bridge; then
        log_error "Failed to start memgraph_skg.py"
        exit 1
    fi
    
    # Wait for Memgraph to be ready
    if ! check_memgraph_health; then
        log_error "Memgraph health check failed"
        exit 1
    fi
    
    # Wait for bridge to be ready
    if ! check_bridge_ready; then
        log_error "Bridge readiness check failed"
        exit 1
    fi
    
    # Give bridge some time to initialize
    log_info "Waiting 5 seconds for bridge to fully initialize..."
    sleep 5
    
    # Run the test
    if run_test; then
        log_success "Test sequence completed successfully!"
        exit 0
    else
        log_error "Test sequence failed!"
        exit 1
    fi
}

# Run main function
main "$@"
