#!/bin/bash

# ===================================================
# Process Cleanup Script
# ===================================================
# This script forcefully stops all related Python processes
# Use this if Ctrl+C doesn't properly stop the test sequence
# ===================================================

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

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

echo "🧹 NATS-Memgraph Process Cleanup"
echo "================================="

# Check for running processes
log_info "Checking for running processes..."

memgraph_processes=$(pgrep -f "memgraph_skg.py" 2>/dev/null || true)
test_processes=$(pgrep -f "test_replay_utility.py" 2>/dev/null || true)
replay_processes=$(pgrep -f "replay_utility" 2>/dev/null || true)

total_processes=0

if [[ -n "$memgraph_processes" ]]; then
    echo "  Found memgraph_skg.py processes: $memgraph_processes"
    total_processes=$((total_processes + $(echo "$memgraph_processes" | wc -w)))
fi

if [[ -n "$test_processes" ]]; then
    echo "  Found test_replay_utility.py processes: $test_processes"
    total_processes=$((total_processes + $(echo "$test_processes" | wc -w)))
fi

if [[ -n "$replay_processes" ]]; then
    echo "  Found replay_utility processes: $replay_processes"
    total_processes=$((total_processes + $(echo "$replay_processes" | wc -w)))
fi

if [[ $total_processes -eq 0 ]]; then
    log_success "No related processes found running"
    exit 0
fi

echo "  Total processes found: $total_processes"

# Ask for confirmation
echo ""
read -p "Do you want to kill these processes? (y/N): " -n 1 -r
echo ""

if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    log_info "Cancelled by user"
    exit 0
fi

# Kill processes gracefully first
log_info "Attempting graceful shutdown..."

if [[ -n "$memgraph_processes" ]]; then
    echo "$memgraph_processes" | xargs kill -TERM 2>/dev/null || true
fi

if [[ -n "$test_processes" ]]; then
    echo "$test_processes" | xargs kill -TERM 2>/dev/null || true
fi

if [[ -n "$replay_processes" ]]; then
    echo "$replay_processes" | xargs kill -TERM 2>/dev/null || true
fi

# Wait for graceful shutdown
log_info "Waiting 3 seconds for graceful shutdown..."
sleep 3

# Check if processes are still running
remaining_processes=$(pgrep -f "memgraph_skg.py|test_replay_utility.py|replay_utility" 2>/dev/null || true)

if [[ -n "$remaining_processes" ]]; then
    log_warning "Some processes still running, force killing..."
    echo "$remaining_processes" | xargs kill -KILL 2>/dev/null || true
    sleep 1
fi

# Final verification
final_check=$(pgrep -f "memgraph_skg.py|test_replay_utility.py|replay_utility" 2>/dev/null || true)

if [[ -n "$final_check" ]]; then
    log_error "Some processes could not be killed: $final_check"
    echo "You may need to run: sudo kill -9 $final_check"
    exit 1
else
    log_success "All processes stopped successfully"
fi

# Clean up PID file
if [[ -f "logs/memgraph_skg.pid" ]]; then
    log_info "Removing PID file..."
    rm -f "logs/memgraph_skg.pid"
fi

log_success "Cleanup completed!"
