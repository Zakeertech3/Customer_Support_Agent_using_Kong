import os
import sys
import time
import subprocess
import requests
from pathlib import Path
from app.config import config
from app.utils.chromadb_init import chromadb_manager

def wait_for_service(url, service_name, timeout=60):
    print(f"Waiting for {service_name} to be ready...")
    start_time = time.time()
    
    while time.time() - start_time < timeout:
        try:
            response = requests.get(url, timeout=5)
            if response.status_code in [200, 404]:
                print(f"{service_name} is ready!")
                return True
        except:
            pass
        time.sleep(2)
    
    print(f"Timeout waiting for {service_name}")
    return False

def start_docker_services():
    print("Starting Docker services...")
    
    try:
        result = subprocess.run(
            ["docker-compose", "up", "-d", "kong-database", "kong", "chromadb"],
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            print(f"Failed to start Docker services: {result.stderr}")
            return False
        
        print("Docker services started successfully!")
        return True
        
    except FileNotFoundError:
        print("Docker Compose not found. Please install Docker and Docker Compose.")
        return False

def initialize_chromadb():
    print("Initializing ChromaDB...")
    
    if not wait_for_service(config.chromadb.url + "/api/v1/heartbeat", "ChromaDB"):
        return False
    
    return chromadb_manager.initialize()

def deploy_kong_configuration():
    print("Deploying Kong configuration...")
    
    if not wait_for_service(config.kong.admin_url + "/status", "Kong Admin API"):
        return False
    
    try:
        result = subprocess.run(
            [sys.executable, "scripts/deploy_kong_config.py"],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            print("Kong configuration deployed successfully!")
            return True
        else:
            print(f"Failed to deploy Kong configuration: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"Error deploying Kong configuration: {e}")
        return False

def start_application_services():
    print("Starting application services...")
    
    backend_cmd = [sys.executable, "main.py"]
    frontend_cmd = ["streamlit", "run", "streamlit_app.py", "--server.port", str(config.server.streamlit_port)]
    
    try:
        print("Starting FastAPI backend...")
        backend_process = subprocess.Popen(backend_cmd)
        
        time.sleep(5)
        
        if not wait_for_service(config.server.backend_url + "/health", "Backend API"):
            backend_process.terminate()
            return False
        
        print("Starting Streamlit frontend...")
        frontend_process = subprocess.Popen(frontend_cmd)
        
        time.sleep(5)
        
        if not wait_for_service(f"http://localhost:{config.server.streamlit_port}", "Frontend"):
            backend_process.terminate()
            frontend_process.terminate()
            return False
        
        print("Application services started successfully!")
        print(f"Backend API: {config.server.backend_url}")
        print(f"Frontend: http://localhost:{config.server.streamlit_port}")
        print(f"Kong Admin: {config.kong.admin_url}")
        print(f"Kong Proxy: {config.kong.proxy_url}")
        
        return True
        
    except Exception as e:
        print(f"Error starting application services: {e}")
        return False

def main():
    print("Kong Support Agent Startup Script")
    print("=" * 40)
    
    steps = [
        ("Starting Docker services", start_docker_services),
        ("Initializing ChromaDB", initialize_chromadb),
        ("Deploying Kong configuration", deploy_kong_configuration),
        ("Starting application services", start_application_services)
    ]
    
    for step_name, step_func in steps:
        print(f"\n{step_name}...")
        if not step_func():
            print(f"Failed at step: {step_name}")
            sys.exit(1)
        print(f"✓ {step_name} completed")
    
    print("\n" + "=" * 40)
    print("All services started successfully!")
    print("The Kong Support Agent is now running.")
    print("\nPress Ctrl+C to stop all services.")
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nShutting down services...")
        subprocess.run(["docker-compose", "down"])
        print("Services stopped.")

if __name__ == "__main__":
    main()