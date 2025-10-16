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
        'mgclient': 'Memgraph client',
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
            # Try to get version, fallback to 'Available' if no version attribute
            try:
                version = getattr(module, '__version__', 'Available')
                print(f"✅ {package} ({description}): {version}")
            except:
                print(f"✅ {package} ({description}): Available")
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
        import mgclient
        
        # Try to connect to default Memgraph port
        conn = mgclient.connect(host='localhost', port=7687)
        conn.close()
        print("✅ Memgraph: Connection successful")
        return True
    except ImportError:
        print("❌ Memgraph: mgclient not available")
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