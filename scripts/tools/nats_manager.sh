#!/bin/bash

# NATS Server Manager for macOS
# Simple script to start, stop, and check status of NATS server

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
NATS_PORT=4222
PID_FILE="/tmp/nats_server.pid"

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

# Check if NATS server is running
is_running() {
    if lsof -i :$NATS_PORT &> /dev/null; then
        return 0
    else
        return 1
    fi
}

# Get NATS server PID
get_pid() {
    lsof -ti :$NATS_PORT 2>/dev/null || echo ""
}

# Start NATS server
start_nats() {
    if is_running; then
        log_warning "NATS server is already running on port $NATS_PORT"
        show_status
        return 0
    fi
    
    log_info "Starting NATS server on localhost:$NATS_PORT..."
    
    # Start NATS server in background
    nohup nats-server --port $NATS_PORT > /tmp/nats_server.log 2>&1 &
    local nats_pid=$!
    
    # Save PID
    echo $nats_pid > $PID_FILE
    
    # Wait for server to start
    sleep 2
    
    if is_running; then
        log_success "NATS server started successfully (PID: $nats_pid)"
        log_info "Log file: /tmp/nats_server.log"
        return 0
    else
        log_error "Failed to start NATS server"
        log_error "Check log file: /tmp/nats_server.log"
        return 1
    fi
}

# Stop NATS server
stop_nats() {
    if ! is_running; then
        log_warning "NATS server is not running"
        return 0
    fi
    
    log_info "Stopping NATS server..."
    
    # Try graceful shutdown first
    local pid=$(get_pid)
    if [[ -n "$pid" ]]; then
        log_info "Sending SIGTERM to PID: $pid"
        kill $pid
        
        # Wait for graceful shutdown
        for i in {1..10}; do
            if ! is_running; then
                log_success "NATS server stopped gracefully"
                rm -f $PID_FILE
                return 0
            fi
            sleep 1
        done
        
        # Force kill if still running
        if is_running; then
            log_warning "Force killing NATS server..."
            kill -9 $pid
            sleep 1
            if ! is_running; then
                log_success "NATS server force stopped"
                rm -f $PID_FILE
                return 0
            fi
        fi
    fi
    
    # Fallback: kill all nats-server processes
    pkill nats-server 2>/dev/null || true
    sleep 1
    
    if ! is_running; then
        log_success "NATS server stopped"
        rm -f $PID_FILE
        return 0
    else
        log_error "Failed to stop NATS server"
        return 1
    fi
}

# Restart NATS server
restart_nats() {
    log_info "Restarting NATS server..."
    stop_nats
    sleep 1
    start_nats
}

# Show NATS server status
show_status() {
    echo ""
    log_info "NATS Server Status:"
    echo "==================="
    
    # Check if nats-server command exists
    if command -v nats-server &> /dev/null; then
        echo "✅ NATS server is installed"
        echo "   Version: $(nats-server --version 2>/dev/null || echo 'Unknown')"
    else
        echo "❌ NATS server is not installed"
        echo "   Run: brew install nats-server"
    fi
    
    # Check if running
    if is_running; then
        echo "✅ NATS server is running on port $NATS_PORT"
        local pid=$(get_pid)
        echo "   PID: $pid"
        echo "   Process: $(ps -p $pid -o comm= 2>/dev/null || echo 'Unknown')"
        
        # Show connection info
        echo "   Connections: $(lsof -i :$NATS_PORT | wc -l | tr -d ' ') - 1"
    else
        echo "❌ NATS server is not running"
    fi
    
    # Show log file info
    if [[ -f "/tmp/nats_server.log" ]]; then
        echo "📄 Log file: /tmp/nats_server.log"
        echo "   Size: $(ls -lh /tmp/nats_server.log | awk '{print $5}')"
        echo "   Last modified: $(ls -l /tmp/nats_server.log | awk '{print $6, $7, $8}')"
    fi
    
    echo ""
}

# Test NATS connection
test_connection() {
    log_info "Testing NATS server connection..."
    
    if ! is_running; then
        log_error "NATS server is not running"
        return 1
    fi
    
    # Try to connect using telnet
    if echo "quit" | timeout 5 telnet localhost $NATS_PORT &> /dev/null; then
        log_success "NATS server connection test passed"
        return 0
    else
        log_error "NATS server connection test failed"
        return 1
    fi
}

# Show logs
show_logs() {
    if [[ -f "/tmp/nats_server.log" ]]; then
        log_info "NATS Server Logs (last 20 lines):"
        echo "=================================="
        tail -20 /tmp/nats_server.log
    else
        log_warning "No log file found at /tmp/nats_server.log"
    fi
}

# Show help
show_help() {
    echo "NATS Server Manager for macOS"
    echo "============================="
    echo ""
    echo "Usage: $0 [COMMAND]"
    echo ""
    echo "Commands:"
    echo "  start     Start NATS server on localhost:$NATS_PORT"
    echo "  stop      Stop NATS server"
    echo "  restart   Restart NATS server"
    echo "  status    Show NATS server status"
    echo "  test      Test NATS server connection"
    echo "  logs      Show recent logs"
    echo "  help      Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 start    # Start NATS server"
    echo "  $0 status   # Check if running"
    echo "  $0 test     # Test connection"
    echo "  $0 stop     # Stop NATS server"
    echo ""
}

# Main function
main() {
    case "${1:-status}" in
        start)
            start_nats
            ;;
        stop)
            stop_nats
            ;;
        restart)
            restart_nats
            ;;
        status)
            show_status
            ;;
        test)
            test_connection
            ;;
        logs)
            show_logs
            ;;
        help|--help|-h)
            show_help
            ;;
        *)
            log_error "Unknown command: $1"
            echo ""
            show_help
            exit 1
            ;;
    esac
}

# Run main function
main "$@"
