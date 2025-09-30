import os
import sys
import subprocess
from pathlib import Path

def check_requirements():
    print("Checking system requirements...")
    
    required_commands = ['docker', 'docker-compose', 'python']
    missing_commands = []
    
    for cmd in required_commands:
        try:
            subprocess.run([cmd, '--version'], capture_output=True, check=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            missing_commands.append(cmd)
    
    if missing_commands:
        print(f"Missing required commands: {missing_commands}")
        print("Please install the missing dependencies and try again.")
        return False
    
    print("System requirements check passed!")
    return True

def install_python_dependencies():
    print("Installing Python dependencies...")
    
    try:
        subprocess.run([sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'], check=True)
        print("Python dependencies installed successfully!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Failed to install Python dependencies: {e}")
        return False

def setup_environment():
    print("Setting up environment configuration...")
    
    env_file = Path('.env')
    env_example = Path('.env.example')
    
    if not env_file.exists() and env_example.exists():
        print("Creating .env file from .env.example...")
        with open(env_example, 'r') as src, open(env_file, 'w') as dst:
            content = src.read()
            dst.write(content)
        
        print("Please update the .env file with your actual configuration values.")
        print("Especially important: GROQ_API_KEY")
        return True
    elif env_file.exists():
        print(".env file already exists.")
        return True
    else:
        print("No .env.example file found. Please create environment configuration manually.")
        return False

def create_directories():
    print("Creating necessary directories...")
    
    directories = [
        'app/models',
        'app/routes', 
        'app/services',
        'app/utils',
        'scripts',
        'kong',
        'logs'
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
    
    print("Directories created successfully!")
    return True

def validate_configuration():
    print("Validating configuration...")
    
    try:
        result = subprocess.run([sys.executable, 'scripts/validate_environment.py'], 
                              capture_output=True, text=True)
        
        if result.returncode == 0:
            print("Configuration validation passed!")
            return True
        else:
            print("Configuration validation failed:")
            print(result.stdout)
            print(result.stderr)
            return False
            
    except Exception as e:
        print(f"Error during configuration validation: {e}")
        return False

def main():
    print("Kong Support Agent Setup Script")
    print("=" * 40)
    
    setup_steps = [
        ("Checking system requirements", check_requirements),
        ("Creating directories", create_directories),
        ("Setting up environment", setup_environment),
        ("Installing Python dependencies", install_python_dependencies),
        ("Validating configuration", validate_configuration)
    ]
    
    for step_name, step_func in setup_steps:
        print(f"\n{step_name}...")
        if not step_func():
            print(f"Setup failed at step: {step_name}")
            sys.exit(1)
        print(f"✓ {step_name} completed")
    
    print("\n" + "=" * 40)
    print("Setup completed successfully!")
    print("\nNext steps:")
    print("1. Update your .env file with the correct GROQ_API_KEY")
    print("2. Run 'python scripts/startup.py' to start all services")
    print("3. Or run 'docker-compose up -d' to start infrastructure services only")
    print("\nFor configuration summary, run: python scripts/config_summary.py")

if __name__ == "__main__":
    main()