import os
import sys
import subprocess
import time
import json
from pathlib import Path
from typing import Dict, Any, List

sys.path.append(str(Path(__file__).parent.parent))

from app.services.environment_service import environment_service

class EnvironmentSetup:
    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.env_file = self.project_root / ".env"
        
    def check_prerequisites(self) -> Dict[str, Any]:
        prerequisites = {
            "docker": self._check_docker(),
            "docker_compose": self._check_docker_compose(),
            "deck": self._check_deck_cli(),
            "python_deps": self._check_python_dependencies()
        }
        
        all_met = all(prerequisites.values())
        
        return {
            "all_met": all_met,
            "details": prerequisites
        }
    
    def _check_docker(self) -> bool:
        try:
            result = subprocess.run(["docker", "--version"], capture_output=True, text=True)
            return result.returncode == 0
        except FileNotFoundError:
            return False
    
    def _check_docker_compose(self) -> bool:
        try:
            result = subprocess.run(["docker-compose", "--version"], capture_output=True, text=True)
            return result.returncode == 0
        except FileNotFoundError:
            return False
    
    def _check_deck_cli(self) -> bool:
        try:
            result = subprocess.run(["deck", "version"], capture_output=True, text=True)
            return result.returncode == 0
        except FileNotFoundError:
            return False
    
    def _check_python_dependencies(self) -> bool:
        try:
            import fastapi
            import streamlit
            import chromadb
            import requests
            return True
        except ImportError:
            return False
    
    def create_env_file_if_missing(self) -> bool:
        if not self.env_file.exists():
            print(f"Creating .env file at: {self.env_file}")
            
            template = environment_service.generate_env_template()
            
            with open(self.env_file, 'w') as f:
                f.write(template)
            
            print("✓ .env file created with default template")
            print("⚠️  Please update the GROQ_API_KEY and other required values")
            return True
        else:
            print("✓ .env file already exists")
            return False
    
    def validate_configuration(self) -> Dict[str, Any]:
        validation = environment_service.validate_environment()
        
        if not validation["valid"]:
            print("⚠️  Environment validation failed!")
            print(f"Missing required variables: {validation['missing_required']}")
            
            for var in validation["missing_required"]:
                print(f"  - {var}")
        
        return validation
    
    def start_infrastructure(self) -> bool:
        print("Starting infrastructure services...")
        
        try:
            os.chdir(self.project_root)
            
            result = subprocess.run([
                "docker-compose", "up", "-d", 
                "kong-database", "kong-migrations", "kong", "chromadb"
            ], capture_output=True, text=True)
            
            if result.returncode == 0:
                print("✓ Infrastructure services started")
                
                print("Waiting for services to be ready...")
                time.sleep(30)
                
                return True
            else:
                print(f"✗ Failed to start infrastructure: {result.stderr}")
                return False
                
        except Exception as e:
            print(f"✗ Error starting infrastructure: {e}")
            return False
    
    def install_python_dependencies(self) -> bool:
        print("Installing Python dependencies...")
        
        try:
            result = subprocess.run([
                sys.executable, "-m", "pip", "install", "-r", "requirements.txt"
            ], capture_output=True, text=True, cwd=self.project_root)
            
            if result.returncode == 0:
                print("✓ Python dependencies installed")
                return True
            else:
                print(f"✗ Failed to install dependencies: {result.stderr}")
                return False
                
        except Exception as e:
            print(f"✗ Error installing dependencies: {e}")
            return False
    
    def generate_setup_commands(self) -> List[str]:
        commands = []
        
        prerequisites = self.check_prerequisites()
        
        if not prerequisites["details"]["docker"]:
            commands.append("# Install Docker Desktop from https://www.docker.com/products/docker-desktop")
        
        if not prerequisites["details"]["deck"]:
            commands.extend([
                "# Install decK CLI tool:",
                "# Windows: Download from https://github.com/Kong/deck/releases",
                "# Or use: curl -sL https://github.com/Kong/deck/releases/latest/download/deck_windows_amd64.tar.gz | tar -xz",
            ])
        
        if not prerequisites["details"]["python_deps"]:
            commands.append("pip install -r requirements.txt")
        
        commands.extend([
            "",
            "# Start infrastructure services:",
            "docker-compose up -d kong-database kong-migrations kong chromadb",
            "",
            "# Wait for services to start (30 seconds)",
            "",
            "# Initialize configuration:",
            "python scripts/initialize_configuration.py",
            "",
            "# Start application services:",
            "python main.py  # Backend (in one terminal)",
            "streamlit run streamlit_app.py  # Frontend (in another terminal)"
        ])
        
        return commands
    
    def run_full_setup(self) -> bool:
        print("Kong Support Agent - Environment Setup")
        print("=" * 50)
        
        print("\n1. Checking prerequisites...")
        prerequisites = self.check_prerequisites()
        
        if not prerequisites["all_met"]:
            print("⚠️  Some prerequisites are missing:")
            for name, status in prerequisites["details"].items():
                status_icon = "✓" if status else "✗"
                print(f"  {status_icon} {name}")
            
            print("\nPlease install missing prerequisites and run setup again.")
            return False
        
        print("✓ All prerequisites met")
        
        print("\n2. Setting up environment file...")
        self.create_env_file_if_missing()
        
        print("\n3. Validating configuration...")
        validation = self.validate_configuration()
        
        if not validation["valid"]:
            print("⚠️  Please fix environment configuration and run setup again.")
            return False
        
        print("✓ Configuration validation passed")
        
        print("\n4. Installing Python dependencies...")
        if not self.install_python_dependencies():
            return False
        
        print("\n5. Starting infrastructure services...")
        if not self.start_infrastructure():
            return False
        
        print("\n6. Running configuration initialization...")
        try:
            from scripts.initialize_configuration import ConfigurationInitializer
            
            initializer = ConfigurationInitializer()
            results = initializer.run_initialization()
            
            if results.get("overall_success", False):
                print("✓ Configuration initialization completed successfully")
                return True
            else:
                print("✗ Configuration initialization failed")
                return False
                
        except Exception as e:
            print(f"✗ Configuration initialization error: {e}")
            return False
    
    def print_manual_commands(self):
        print("\nManual Setup Commands:")
        print("=" * 30)
        
        commands = self.generate_setup_commands()
        for command in commands:
            print(command)

def main():
    setup = EnvironmentSetup()
    
    if len(sys.argv) > 1 and sys.argv[1] == "--manual":
        setup.print_manual_commands()
        return
    
    success = setup.run_full_setup()
    
    if success:
        print("\n" + "=" * 50)
        print("✓ Environment setup completed successfully!")
        print("You can now start the application:")
        print("  Backend:  python main.py")
        print("  Frontend: streamlit run streamlit_app.py")
        print("=" * 50)
    else:
        print("\n" + "=" * 50)
        print("✗ Environment setup failed!")
        print("Please check the errors above and try again.")
        print("For manual setup commands, run: python scripts/setup_environment.py --manual")
        print("=" * 50)
        sys.exit(1)

if __name__ == "__main__":
    main()
