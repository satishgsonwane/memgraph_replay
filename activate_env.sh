#!/bin/bash
# ===================================================
# Quick Activation Script
# ===================================================
# Run this script to activate the conda environment
# ===================================================

echo "🚀 Activating conda environment: memgraph_replay"
conda activate memgraph_replay

if [[ $? -eq 0 ]]; then
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
    echo ""
    echo "🧪 Test environment:"
    echo "  python test_environment.py          # Test all dependencies"
else
    echo "❌ Failed to activate environment"
    exit 1
fi