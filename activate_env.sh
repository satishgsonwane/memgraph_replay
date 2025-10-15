#!/bin/bash

# ===================================================
# Quick Activation Script
# ===================================================
# Run this script to activate the conda environment
# ===================================================

ENV_NAME="memgraph_replay"

echo "🚀 Activating conda environment: ${ENV_NAME}"
conda activate ${ENV_NAME}

if [[ $? -eq 0 ]]; then
    echo "✅ Environment activated successfully!"
    echo ""
    echo "📋 Available commands:"
    echo "  python test_environment.py                       # Test environment setup"
    echo "  python memgraph_skg.py                           # Start the bridge service"
    echo "  python -m replay_utility capture                 # Capture NATS messages"
    echo "  python -m replay_utility replay                  # Replay captured messages"
    echo "  python scripts/setup/init_usd_scene.py           # Initialize USD scene"
    echo "  python scripts/tools/check_usd_nodes.py          # Check USD nodes"
    echo "  ./run_test_sequence.sh                           # Run test sequence"
    echo "  ./scripts/tools/cleanup_processes.sh             # Clean up processes"
    echo ""
    echo "🔧 To deactivate: conda deactivate"
    echo "📁 Current directory: $(pwd)"
else
    echo "❌ Failed to activate environment"
    echo "💡 Make sure to run ./setup_conda_env.sh first"
    exit 1
fi
