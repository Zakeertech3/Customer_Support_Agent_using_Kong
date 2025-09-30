import os
import sys
import subprocess
import time
import requests
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def quick_start():
    print("Kong Support Agent - Quick Start (Simplified)")
    print("=" * 50)
    
    os.chdir(project_root)
    
    print("1. Stopping existing services...")
    subprocess.run(["docker-compose", "down"], capture_output=True)
    
    print("2. Starting basic services...")
    
    # Start database
    result = subprocess.run([
        "docker-compose", "up", "-d", "kong-database"
    ], capture_output=True, text=True)
    
    if result.returncode != 0:
        print(f"Failed to start database: {result.stderr}")
        return False
    
    print("   Database starting...")
    time.sleep(15)
    
    # Run migrations
    result = subprocess.run([
        "docker-compose", "up", "kong-migrations"
    ], capture_output=True, text=True)
    
    print("   Migrations completed")
    time.sleep(5)
    
    # Start ChromaDB
    result = subprocess.run([
        "docker-compose", "up", "-d", "chromadb"
    ], capture_output=True, text=True)
    
    print("   ChromaDB starting...")
    time.sleep(10)
    
    # Start Kong (simplified)
    result = subprocess.run([
        "docker-compose", "up", "-d", "kong"
    ], capture_output=True, text=True)
    
    print("   Kong Gateway starting...")
    time.sleep(20)
    
    # Test services
    print("\n3. Testing services...")
    
    # Test ChromaDB
    try:
        response = requests.get("http://localhost:8003/api/v1/version", timeout=5)
        if response.status_code == 200:
            print("✓ ChromaDB: OK")
        else:
            print(f"⚠️  ChromaDB: Status {response.status_code}")
    except Exception as e:
        print(f"✗ ChromaDB: {e}")
    
    # Test Kong
    try:
        response = requests.get("http://localhost:8001/status", timeout=5)
        if response.status_code == 200:
            print("✓ Kong Admin: OK")
        else:
            print(f"⚠️  Kong Admin: Status {response.status_code}")
    except Exception as e:
        print(f"✗ Kong Admin: {e}")
    
    try:
        response = requests.get("http://localhost:8000", timeout=5)
        if response.status_code in [200, 404]:  # 404 is normal for Kong proxy root
            print("✓ Kong Proxy: OK")
        else:
            print(f"⚠️  Kong Proxy: Status {response.status_code}")
    except Exception as e:
        print(f"✗ Kong Proxy: {e}")
    
    print("\n4. Next steps:")
    print("   - Run: python scripts/initialize_configuration.py")
    print("   - Run: python main.py")
    print("   - Run: streamlit run streamlit_app.py")
    
    return True

if __name__ == "__main__":
    quick_start()
