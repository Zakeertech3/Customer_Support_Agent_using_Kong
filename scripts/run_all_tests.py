#!/usr/bin/env python3

import sys
import os
import subprocess
import time
from typing import Dict, List, Any

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def run_command(command: List[str], description: str, timeout: int = 300) -> Dict[str, Any]:
    print(f"\n{'='*60}")
    print(f"Running: {description}")
    print(f"Command: {' '.join(command)}")
    print(f"{'='*60}")
    
    start_time = time.time()
    
    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        )
        
        execution_time = time.time() - start_time
        
        print(result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)
        
        success = result.returncode == 0
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"\n{status} - {description} ({execution_time:.2f}s)")
        
        return {
            "description": description,
            "command": ' '.join(command),
            "success": success,
            "return_code": result.returncode,
            "execution_time": execution_time,
            "stdout": result.stdout,
            "stderr": result.stderr
        }
        
    except subprocess.TimeoutExpired:
        execution_time = time.time() - start_time
        print(f"⏰ TIMEOUT - {description} ({execution_time:.2f}s)")
        return {
            "description": description,
            "command": ' '.join(command),
            "success": False,
            "return_code": -1,
            "execution_time": execution_time,
            "error": "Timeout"
        }
        
    except Exception as e:
        execution_time = time.time() - start_time
        print(f"💥 ERROR - {description}: {e}")
        return {
            "description": description,
            "command": ' '.join(command),
            "success": False,
            "return_code": -1,
            "execution_time": execution_time,
            "error": str(e)
        }


def check_dependencies() -> bool:
    print("Checking dependencies...")
    
    required_packages = [
        "fastapi",
        "streamlit", 
        "textblob",
        "vaderSentiment",
        "pydantic",
        "httpx",
        "psutil"
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package.replace("-", "_"))
            print(f"✅ {package}")
        except ImportError:
            print(f"❌ {package} - MISSING")
            missing_packages.append(package)
    
    if missing_packages:
        print(f"\n⚠️ Missing packages: {', '.join(missing_packages)}")
        print("Install with: pip install " + " ".join(missing_packages))
        return False
    
    print("✅ All dependencies available")
    return True


def run_all_tests() -> Dict[str, Any]:
    print("Kong Support Agent - Comprehensive Testing Suite")
    print("="*80)
    
    if not check_dependencies():
        return {"success": False, "error": "Missing dependencies"}
    
    test_results = []
    
    test_commands = [
        {
            "command": [sys.executable, "tests/test_unit_comprehensive.py"],
            "description": "Unit Tests - Complexity, Sentiment, Escalation",
            "timeout": 120
        },
        {
            "command": [sys.executable, "tests/test_comprehensive_demo.py"],
            "description": "Demo Scenarios - Simple, Complex, Negative Sentiment",
            "timeout": 180
        },
        {
            "command": [sys.executable, "tests/test_kong_integration.py"],
            "description": "Kong Gateway Integration Tests",
            "timeout": 300
        },
        {
            "command": [sys.executable, "scripts/test_performance.py"],
            "description": "Performance Testing - Response Times & Memory",
            "timeout": 240
        },
        {
            "command": [sys.executable, "scripts/test_concurrent_performance.py"],
            "description": "Concurrent Performance Testing",
            "timeout": 300
        },
        {
            "command": [sys.executable, "scripts/generate_demo_data.py"],
            "description": "Demo Data Generation",
            "timeout": 60
        }
    ]
    
    for test_config in test_commands:
        result = run_command(
            test_config["command"],
            test_config["description"],
            test_config.get("timeout", 300)
        )
        test_results.append(result)
    
    return {
        "success": all(result["success"] for result in test_results),
        "results": test_results,
        "total_tests": len(test_results),
        "passed_tests": sum(1 for result in test_results if result["success"]),
        "failed_tests": sum(1 for result in test_results if not result["success"])
    }


def print_final_summary(results: Dict[str, Any]):
    print("\n" + "="*80)
    print("FINAL TEST SUMMARY")
    print("="*80)
    
    if not results["success"]:
        if "error" in results:
            print(f"❌ Testing failed: {results['error']}")
            return
    
    print(f"Total tests: {results['total_tests']}")
    print(f"Passed: {results['passed_tests']}")
    print(f"Failed: {results['failed_tests']}")
    
    print(f"\nTest Results:")
    for result in results["results"]:
        status = "✅" if result["success"] else "❌"
        time_str = f"{result['execution_time']:.2f}s"
        print(f"  {status} {result['description']} ({time_str})")
        
        if not result["success"]:
            if "error" in result:
                print(f"      Error: {result['error']}")
            elif result["return_code"] != 0:
                print(f"      Return code: {result['return_code']}")
    
    total_time = sum(result["execution_time"] for result in results["results"])
    print(f"\nTotal execution time: {total_time:.2f}s")
    
    if results["success"]:
        print(f"\n🎉 ALL TESTS PASSED!")
        print(f"\n✅ Testing and Demo Data Setup - COMPLETED")
        print(f"   ✓ Unit tests for complexity analysis, sentiment detection, and escalation logic")
        print(f"   ✓ Integration tests for Kong Gateway routing and plugin functionality")
        print(f"   ✓ Demo query scenarios (simple, complex, negative sentiment)")
        print(f"   ✓ Performance testing for response time and concurrent user handling")
        print(f"   ✓ Demo data generation for comprehensive testing scenarios")
    else:
        print(f"\n⚠️ SOME TESTS FAILED")
        print(f"   Check individual test outputs above for details")
        print(f"   Note: Kong Gateway tests may fail if Kong is not running")
        print(f"   Note: API integration tests may fail if backend is not running")


def main():
    try:
        results = run_all_tests()
        print_final_summary(results)
        return results["success"]
    except KeyboardInterrupt:
        print("\n⚠️ Testing interrupted by user")
        return False
    except Exception as e:
        print(f"\n❌ Testing failed with exception: {e}")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)