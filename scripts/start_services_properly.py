import os
import sys
import subprocess
import time
import requests
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def wait_for_service(url, service_name, max_wait=120, check_interval=5):
    """Wait for a service to become available"""
    print(f"Waiting for {service_name} at {url}...")
    
    for attempt in range(max_wait // check_interval):
        try:
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                print(f"✓ {service_name} is ready!")
                return True
        except Exception as e:
            print(f"  Attempt {attempt + 1}: {service_name} not ready yet... ({e})")
        
        time.sleep(check_interval)
    
    print(f"✗ {service_name} failed to start within {max_wait} seconds")
    return False

def check_docker_running():
    """Check if Docker is running"""
    try:
        result = subprocess.run(["docker", "ps"], capture_output=True, text=True)
        return result.returncode == 0
    except FileNotFoundError:
        print("✗ Docker is not installed or not in PATH")
        return False

def start_services_step_by_step():
    print("Kong Support Agent - Proper Service Startup")
    print("=" * 60)
    
    # Check Docker
    if not check_docker_running():
        print("✗ Docker is not running. Please start Docker Desktop first.")
        return False
    
    print("✓ Docker is running")
    
    # Change to project directory
    os.chdir(project_root)
    
    # Stop any existing services
    print("\n1. Stopping existing services...")
    subprocess.run(["docker-compose", "down"], capture_output=True)
    time.sleep(5)
    
    # Start database first
    print("\n2. Starting PostgreSQL database...")
    result = subprocess.run([
        "docker-compose", "up", "-d", "kong-database"
    ], capture_output=True, text=True)
    
    if result.returncode != 0:
        print(f"✗ Failed to start database: {result.stderr}")
        return False
    
    # Wait for database
    if not wait_for_service("http://localhost:5432", "PostgreSQL", max_wait=60):
        print("Note: PostgreSQL health check failed, but continuing...")
    
    # Start migrations
    print("\n3. Running Kong migrations...")
    result = subprocess.run([
        "docker-compose", "up", "kong-migrations"
    ], capture_output=True, text=True)
    
    if result.returncode != 0:
        print(f"⚠️  Migrations warning: {result.stderr}")
    else:
        print("✓ Kong migrations completed")
    
    time.sleep(10)
    
    # Start ChromaDB
    print("\n4. Starting ChromaDB...")
    result = subprocess.run([
        "docker-compose", "up", "-d", "chromadb"
    ], capture_output=True, text=True)
    
    if result.returncode != 0:
        print(f"✗ Failed to start ChromaDB: {result.stderr}")
        return False
    
    # Wait for ChromaDB
    if not wait_for_service("http://localhost:8003/api/v1/version", "ChromaDB", max_wait=90):
        print("⚠️  ChromaDB may not be fully ready, but continuing...")
    
    # Start Kong Gateway
    print("\n5. Starting Kong Gateway...")
    result = subprocess.run([
        "docker-compose", "up", "-d", "kong"
    ], capture_output=True, text=True)
    
    if result.returncode != 0:
        print(f"✗ Failed to start Kong: {result.stderr}")
        return False
    
    # Wait for Kong Admin API
    if not wait_for_service("http://localhost:8001/status", "Kong Admin API", max_wait=120):
        print("✗ Kong Gateway failed to start properly")
        return False
    
    # Wait for Kong Proxy
    if not wait_for_service("http://localhost:8000", "Kong Proxy", max_wait=60):
        print("⚠️  Kong Proxy may not be fully ready, but continuing...")
    
    print("\n" + "=" * 60)
    print("✓ All services started successfully!")
    
    # Show service status
    print("\nService Status:")
    print("-" * 30)
    
    services = [
        ("Kong Admin API", "http://localhost:8001/status"),
        ("Kong Proxy", "http://localhost:8000"),
        ("ChromaDB", "http://localhost:8003/api/v1/version"),
    ]
    
    all_healthy = True
    for service_name, url in services:
        try:
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                print(f"✓ {service_name}: OK")
            else:
                print(f"⚠️  {service_name}: Status {response.status_code}")
                all_healthy = False
        except Exception as e:
            print(f"✗ {service_name}: FAIL - {e}")
            all_healthy = False
    
    if all_healthy:
        print("\n🎉 All services are healthy and ready!")
        print("\nNext steps:")
        print("1. Run: python scripts/initialize_configuration.py")
        print("2. Run: python main.py (Backend)")
        print("3. Run: streamlit run streamlit_app.py (Frontend)")
        return True
    else:
        print("\n⚠️  Some services have issues. Check the logs:")
        print("docker-compose logs kong")
        print("docker-compose logs chromadb")
        return False

def show_docker_logs():
    """Show recent Docker logs for debugging"""
    print("\nRecent Docker Logs:")
    print("=" * 40)
    
    services = ["kong", "chromadb", "kong-database"]
    for service in services:
        print(f"\n--- {service.upper()} LOGS ---")
        result = subprocess.run([
            "docker-compose", "logs", "--tail", "10", service
        ], capture_output=True, text=True)
        
        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print(f"STDERR: {result.stderr}")

def main():
    success = start_services_step_by_step()
    
    if not success:
        print("\n" + "=" * 60)
        print("❌ Service startup failed!")
        print("\nTroubleshooting steps:")
        print("1. Check Docker Desktop is running")
        print("2. Check port availability (8001, 8000, 8003, 5432)")
        print("3. Run: docker-compose down && docker system prune -f")
        print("4. Try again")
        
        show_logs = input("\nShow Docker logs for debugging? (y/n): ").lower().strip()
        if show_logs == 'y':
            show_docker_logs()
        
        sys.exit(1)

if __name__ == "__main__":
    main()
