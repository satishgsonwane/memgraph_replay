# NATS-Memgraph Bridge Test Sequence

This document describes how to use the `run_test_sequence.sh` script to test the complete NATS-Memgraph bridge functionality.

## Overview

The test sequence script automates the following process:
1. Starts `memgraph_skg.py` (the NATS-Memgraph bridge service)
2. Waits for Memgraph to be ready and accepting connections
3. Waits for the bridge to fully initialize and connect to NATS servers
4. Runs `test_replay_utility.py` to test data population in Memgraph
5. Cleans up all processes gracefully

## Prerequisites

Before running the test sequence, ensure you have:

1. **Memgraph running**: The script expects Memgraph to be available at `localhost:7687`
2. **NATS server**: 
   - NATS server at `localhost:4222`
3. **Python dependencies**: All required Python packages installed (use `./setup_env.sh`)
4. **Docker**: For the Memgraph container restart functionality

## Usage

### Basic Usage

```bash
# Run the complete test sequence (default: continuous loop with topic-specific rates)
./run_test_sequence.sh

# Run with different modes:
./run_test_sequence.sh --no-loop         # Single replay with topic-specific rates
./run_test_sequence.sh --no-topic-rates  # Continuous loop with global framerate
./run_test_sequence.sh --no-loop --no-topic-rates  # Single replay with global framerate
```

### What the Script Does

1. **Setup Phase**:
   - Creates log directory (`logs/`)
   - Validates script files exist
   - Cleans up any existing processes

2. **Bridge Startup**:
   - Starts `memgraph_skg.py` in background
   - Monitors startup process
   - Performs health checks

3. **Health Checks**:
   - **Memgraph Health**: Verifies Memgraph is accepting connections
   - **Bridge Readiness**: Confirms NATS connections are established

4. **Test Execution**:
   - Runs `test_replay_utility.py`
   - Captures test results and logs
   - Displays summary of results

5. **Cleanup**:
   - Gracefully stops the bridge process
   - Cleans up temporary files
   - Provides final status

## Log Files

The script creates the following log files in the `logs/` directory:

- `memgraph_skg.log`: Output from the bridge service
- `test_replay.log`: Output from the test script
- `memgraph_skg.pid`: Process ID file for cleanup

## Expected Output

### Successful Run

```
[INFO] Starting NATS-Memgraph Bridge Test Sequence
[INFO] Mode: Continuous loop replay with topic-specific rates (default)
[INFO] Setting up test environment...
[SUCCESS] Setup completed
[INFO] Starting memgraph_skg.py...
[INFO] memgraph_skg.py started with PID: 12345
[SUCCESS] memgraph_skg.py started successfully
[INFO] Checking Memgraph health...
[SUCCESS] Memgraph is ready and accepting connections
[INFO] Checking if NATS-Memgraph bridge is ready...
[SUCCESS] NATS-Memgraph bridge is ready
[INFO] Running test_replay_utility.py...
[INFO] Loop mode enabled - replay will run continuously
[INFO] Topic-specific rates enabled - each topic will use its configured rate
[SUCCESS] test_replay_utility.py completed successfully
=== Test Results Summary ===
Testing configuration...
Configuration test passed
Testing JSON format...
JSON format test passed
Capture test passed
Replay test passed
All tests completed!
==========================
[SUCCESS] Test sequence completed successfully!
```

### Error Handling

The script includes comprehensive error handling:

- **Startup Failures**: Detects if memgraph_skg.py fails to start
- **Health Check Failures**: Identifies Memgraph or bridge connection issues
- **Test Failures**: Captures and displays test errors
- **Cleanup**: Ensures proper process termination

## Troubleshooting

### Common Issues

1. **Memgraph Not Ready**:
   ```
   [ERROR] Memgraph failed to become ready after 30 attempts
   ```
   - Check if Memgraph container is running
   - Verify port 7687 is accessible
   - Check Memgraph logs for startup issues

2. **NATS Connection Failed**:
   ```
   [ERROR] Bridge readiness check failed
   ```
   - Verify NATS server is running
   - Check network connectivity to `localhost:4222`

3. **Test Script Failed**:
   ```
   [ERROR] test_replay_utility.py failed
   ```
   - Check test log file for specific errors
   - Verify captured data files exist
   - Ensure proper permissions on data directories

### Manual Cleanup

If the script doesn't clean up properly:

```bash
# Kill any remaining processes
pkill -f memgraph_skg.py

# Remove PID file
rm -f logs/memgraph_skg.pid

# Check for running processes
ps aux | grep memgraph_skg.py
```

## Script Configuration

The script can be customized by modifying these variables at the top:

```bash
# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MEMGRAPH_SCRIPT="$SCRIPT_DIR/memgraph_skg.py"
TEST_SCRIPT="$SCRIPT_DIR/test_replay_utility.py"
LOG_DIR="$SCRIPT_DIR/logs"
```

## Exit Codes

- `0`: Success - All tests passed
- `1`: Failure - Setup, startup, health check, or test failure

## Performance Notes

- Total execution time: Typically 30-60 seconds
- Health checks: 30 attempts with 3-second intervals
- Bridge readiness: 20 attempts with 2-second intervals
- Graceful shutdown: Up to 10 seconds for process termination

This automated test sequence ensures reliable testing of the complete NATS-Memgraph bridge functionality with proper error handling and cleanup.
