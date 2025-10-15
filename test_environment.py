#!/usr/bin/env python3
"""
Environment Test Script

This script verifies that all required dependencies are properly installed
and accessible in the current environment.
"""

import sys
from pathlib import Path

def test_python_version():
    """Test Python version"""
    print("🐍 Testing Python version...")
    version = sys.version_info
    if version.major == 3 and version.minor >= 10:
        print(f"✅ Python {version.major}.{version.minor}.{version.micro} - OK")
        return True
    else:
        print(f"❌ Python {version.major}.{version.minor}.{version.micro} - Need Python 3.10+")
        return False

def test_core_imports():
    """Test core dependency imports"""
    print("\n📦 Testing core dependencies...")
    
    tests = [
        ("mgclient", "Memgraph database client"),
        ("nats", "NATS message bus client"),
        ("orjson", "Fast JSON processing"),
        ("pydantic", "Data validation"),
        ("typing_extensions", "Enhanced typing"),
        ("psutil", "System utilities"),
    ]
    
    all_passed = True
    for module, description in tests:
        try:
            __import__(module)
            print(f"✅ {module} - {description}")
        except ImportError as e:
            print(f"❌ {module} - {description} - {e}")
            all_passed = False
    
    return all_passed

def test_project_imports():
    """Test project module imports"""
    print("\n🏗️  Testing project modules...")
    
    # Add project root to path
    project_root = Path(__file__).parent
    sys.path.insert(0, str(project_root))
    
    tests = [
        ("src.core.config", "Core configuration"),
        ("src.core.interfaces", "Core interfaces"),
        ("src.core.service", "Main service"),
        ("database.repository", "Database layer"),
        ("replay_utility.config", "Replay configuration"),
        ("replay_utility.capture", "Message capture"),
        ("replay_utility.replay", "Message replay"),
    ]
    
    all_passed = True
    for module, description in tests:
        try:
            __import__(module)
            print(f"✅ {module} - {description}")
        except ImportError as e:
            print(f"❌ {module} - {description} - {e}")
            all_passed = False
    
    return all_passed

def test_file_structure():
    """Test project file structure"""
    print("\n📁 Testing project structure...")
    
    required_files = [
        "memgraph_skg.py",
        "requirements.txt",
        "environment.yml",
        "src/core/config.py",
        "src/core/service.py",
        "database/repository.py",
        "replay_utility/capture.py",
        "replay_utility/replay.py",
        "scripts/setup/init_usd_scene.py",
        "scripts/tools/check_usd_nodes.py",
    ]
    
    all_passed = True
    for file_path in required_files:
        if Path(file_path).exists():
            print(f"✅ {file_path}")
        else:
            print(f"❌ {file_path} - Missing")
            all_passed = False
    
    return all_passed

def main():
    """Run all tests"""
    print("🧪 NATS-Memgraph Replay Utility - Environment Test")
    print("=" * 55)
    
    tests = [
        test_python_version,
        test_core_imports,
        test_project_imports,
        test_file_structure,
    ]
    
    results = []
    for test in tests:
        results.append(test())
    
    print("\n" + "=" * 55)
    print("📊 Test Results Summary")
    print("=" * 55)
    
    if all(results):
        print("🎉 All tests passed! Environment is ready.")
        print("\n📋 Next steps:")
        print("  1. Initialize USD scene: python scripts/setup/init_usd_scene.py")
        print("  2. Run test sequence: ./run_test_sequence.sh")
        return 0
    else:
        print("❌ Some tests failed. Please check the errors above.")
        print("\n🔧 Troubleshooting:")
        print("  1. Make sure conda environment is activated: conda activate memgraph_replay")
        print("  2. Reinstall dependencies: pip install -r requirements.txt")
        print("  3. Check project structure and file paths")
        return 1

if __name__ == "__main__":
    sys.exit(main())
