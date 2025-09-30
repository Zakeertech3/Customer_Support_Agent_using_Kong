import os
import sys
import subprocess
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def test_imports():
    print("Testing imports...")
    try:
        from app.config import config
        print("✓ app.config imported successfully")
        
        from app.services.environment_service import environment_service
        print("✓ environment_service imported successfully")
        
        from app.services.chromadb_service import chromadb_service
        print("✓ chromadb_service imported successfully")
        
        return True
    except Exception as e:
        print(f"✗ Import error: {e}")
        return False

def check_environment():
    print("\nChecking environment configuration...")
    try:
        from app.services.environment_service import environment_service
        validation = environment_service.validate_environment()
        
        if validation["valid"]:
            print("✓ Environment validation passed")
        else:
            print(f"⚠️  Missing required variables: {validation['missing_required']}")
        
        return validation["valid"]
    except Exception as e:
        print(f"✗ Environment check error: {e}")
        return False

def stop_conflicting_services():
    print("\nStopping any conflicting Docker services...")
    try:
        # Stop any existing containers that might be using our ports
        subprocess.run(["docker-compose", "down"], capture_output=True, cwd=project_root)
        print("✓ Stopped existing Docker services")
        return True
    except Exception as e:
        print(f"⚠️  Could not stop Docker services: {e}")
        return False

def start_infrastructure():
    print("\nStarting infrastructure services...")
    try:
        os.chdir(project_root)
        
        # Start services one by one to avoid port conflicts
        result = subprocess.run([
            "docker-compose", "up", "-d", 
            "kong-database"
        ], capture_output=True, text=True)
        
        if result.returncode != 0:
            print(f"✗ Failed to start database: {result.stderr}")
            return False
        
        print("✓ Database started")
        
        # Wait a bit for database to be ready
        import time
        time.sleep(10)
        
        # Start migrations
        result = subprocess.run([
            "docker-compose", "up", "-d", 
            "kong-migrations"
        ], capture_output=True, text=True)
        
        print("✓ Migrations started")
        time.sleep(10)
        
        # Start ChromaDB
        result = subprocess.run([
            "docker-compose", "up", "-d", 
            "chromadb"
        ], capture_output=True, text=True)
        
        if result.returncode != 0:
            print(f"✗ Failed to start ChromaDB: {result.stderr}")
            return False
        
        print("✓ ChromaDB started")
        time.sleep(5)
        
        # Start Kong
        result = subprocess.run([
            "docker-compose", "up", "-d", 
            "kong"
        ], capture_output=True, text=True)
        
        if result.returncode != 0:
            print(f"✗ Failed to start Kong: {result.stderr}")
            return False
        
        print("✓ Kong started")
        time.sleep(15)
        
        return True
        
    except Exception as e:
        print(f"✗ Error starting infrastructure: {e}")
        return False

def test_services():
    print("\nTesting service connectivity...")
    import requests
    import time
    
    services_status = {}
    
    # Test Kong Admin API
    try:
        response = requests.get("http://localhost:8001/status", timeout=10)
        services_status["kong_admin"] = response.status_code == 200
        print(f"✓ Kong Admin API: {'OK' if services_status['kong_admin'] else 'FAIL'}")
    except Exception as e:
        services_status["kong_admin"] = False
        print(f"✗ Kong Admin API: FAIL - {e}")
    
    # Test ChromaDB
    try:
        response = requests.get("http://localhost:8003/api/v1/heartbeat", timeout=10)
        services_status["chromadb"] = response.status_code == 200
        print(f"✓ ChromaDB: {'OK' if services_status['chromadb'] else 'FAIL'}")
    except Exception as e:
        services_status["chromadb"] = False
        print(f"✗ ChromaDB: FAIL - {e}")
    
    return all(services_status.values())

def main():
    print("Kong Support Agent - Fix and Test Script")
    print("=" * 50)
    
    # Test imports first
    if not test_imports():
        print("\n❌ Import tests failed. Please check your Python environment.")
        return False
    
    # Check environment
    if not check_environment():
        print("\n⚠️  Environment configuration has issues. Please check your .env file.")
    
    # Stop conflicting services
    stop_conflicting_services()
    
    # Start infrastructure
    if not start_infrastructure():
        print("\n❌ Failed to start infrastructure services.")
        return False
    
    # Test services
    if test_services():
        print("\n🎉 All services are running successfully!")
        print("\nNext steps:")
        print("1. Run: python scripts/initialize_configuration.py")
        print("2. Run: python main.py (in one terminal)")
        print("3. Run: streamlit run streamlit_app.py (in another terminal)")
        return True
    else:
        print("\n❌ Some services are not responding correctly.")
        return False

if __name__ == "__main__":
    success = main()
    if not success:
        sys.exit(1)
