import os
import sys
import requests
import chromadb
from pathlib import Path
from app.config import config
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EnvironmentValidator:
    def __init__(self):
        self.validation_results = {}
    
    def validate_environment_variables(self):
        print("Validating environment variables...")
        
        required_vars = [
            'GROQ_API_KEY',
            'KONG_ADMIN_URL',
            'KONG_PROXY_URL',
            'CHROMADB_URL',
            'BACKEND_URL'
        ]
        
        missing_vars = []
        for var in required_vars:
            if not os.getenv(var):
                missing_vars.append(var)
        
        if missing_vars:
            print(f"Missing required environment variables: {missing_vars}")
            self.validation_results['env_vars'] = False
            return False
        
        print("Environment variables validation passed!")
        self.validation_results['env_vars'] = True
        return True
    
    def validate_groq_api(self):
        print("Validating Groq API connection...")
        
        try:
            headers = {
                'Authorization': f'Bearer {config.groq.api_key}',
                'Content-Type': 'application/json'
            }
            
            test_payload = {
                "model": config.groq.simple_model,
                "messages": [{"role": "user", "content": "Hello"}],
                "max_tokens": 10
            }
            
            response = requests.post(
                'https://api.groq.com/openai/v1/chat/completions',
                headers=headers,
                json=test_payload,
                timeout=30
            )
            
            if response.status_code == 200:
                print("Groq API validation passed!")
                self.validation_results['groq_api'] = True
                return True
            else:
                print(f"Groq API validation failed: {response.status_code} - {response.text}")
                self.validation_results['groq_api'] = False
                return False
                
        except Exception as e:
            print(f"Groq API validation error: {e}")
            self.validation_results['groq_api'] = False
            return False
    
    def validate_kong_gateway(self):
        print("Validating Kong Gateway...")
        
        try:
            admin_response = requests.get(f"{config.kong.admin_url}/status", timeout=10)
            if admin_response.status_code != 200:
                print(f"Kong Admin API not accessible: {admin_response.status_code}")
                self.validation_results['kong'] = False
                return False
            
            proxy_response = requests.get(f"{config.kong.proxy_url}", timeout=10)
            if proxy_response.status_code not in [200, 404]:
                print(f"Kong Proxy not accessible: {proxy_response.status_code}")
                self.validation_results['kong'] = False
                return False
            
            print("Kong Gateway validation passed!")
            self.validation_results['kong'] = True
            return True
            
        except Exception as e:
            print(f"Kong Gateway validation error: {e}")
            self.validation_results['kong'] = False
            return False
    
    def validate_chromadb(self):
        print("Validating ChromaDB connection...")
        
        try:
            client = chromadb.HttpClient(
                host=config.chromadb.host,
                port=config.chromadb.port
            )
            
            client.heartbeat()
            
            test_collection = client.get_or_create_collection("test_validation")
            client.delete_collection("test_validation")
            
            print("ChromaDB validation passed!")
            self.validation_results['chromadb'] = True
            return True
            
        except Exception as e:
            print(f"ChromaDB validation error: {e}")
            self.validation_results['chromadb'] = False
            return False
    
    def validate_file_structure(self):
        print("Validating file structure...")
        
        required_files = [
            '.env',
            'kong/kong.yml',
            'docker-compose.yml',
            'app/config.py',
            'app/utils/chromadb_init.py'
        ]
        
        missing_files = []
        for file_path in required_files:
            if not Path(file_path).exists():
                missing_files.append(file_path)
        
        if missing_files:
            print(f"Missing required files: {missing_files}")
            self.validation_results['file_structure'] = False
            return False
        
        print("File structure validation passed!")
        self.validation_results['file_structure'] = True
        return True
    
    def validate_model_configurations(self):
        print("Validating model configurations...")
        
        models = [
            config.groq.simple_model,
            config.groq.complex_model,
            config.groq.fallback_model
        ]
        
        valid_models = [
            'llama-3.3-70b-versatile',
            'openai/gpt-oss-120b',
            'llama-3.1-8b-instant',
            'llama-3.1-70b-versatile',
            'mixtral-8x7b-32768'
        ]
        
        invalid_models = []
        for model in models:
            if model not in valid_models:
                invalid_models.append(model)
        
        if invalid_models:
            print(f"Invalid model configurations: {invalid_models}")
            print(f"Valid models: {valid_models}")
            self.validation_results['model_config'] = False
            return False
        
        print("Model configurations validation passed!")
        self.validation_results['model_config'] = True
        return True
    
    def validate_ports(self):
        print("Validating port configurations...")
        
        ports_to_check = [
            (config.server.fastapi_port, "FastAPI Backend"),
            (config.server.streamlit_port, "Streamlit Frontend"),
            (config.chromadb.port, "ChromaDB"),
            (8001, "Kong Admin"),
            (8000, "Kong Proxy")
        ]
        
        import socket
        
        for port, service in ports_to_check:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1)
            result = sock.connect_ex(('localhost', port))
            sock.close()
            
            if result == 0:
                print(f"Port {port} ({service}) is in use")
            else:
                print(f"Port {port} ({service}) is available")
        
        self.validation_results['ports'] = True
        return True
    
    def run_full_validation(self):
        print("Running comprehensive environment validation...")
        print("=" * 50)
        
        validations = [
            self.validate_environment_variables,
            self.validate_file_structure,
            self.validate_model_configurations,
            self.validate_ports,
            self.validate_groq_api,
            self.validate_kong_gateway,
            self.validate_chromadb
        ]
        
        all_passed = True
        for validation in validations:
            try:
                result = validation()
                if not result:
                    all_passed = False
            except Exception as e:
                print(f"Validation error: {e}")
                all_passed = False
            print("-" * 30)
        
        print("Validation Summary:")
        print("=" * 50)
        for component, status in self.validation_results.items():
            status_text = "PASS" if status else "FAIL"
            print(f"{component.upper()}: {status_text}")
        
        if all_passed:
            print("\nAll validations passed! Environment is ready.")
            return True
        else:
            print("\nSome validations failed. Please fix the issues above.")
            return False

if __name__ == "__main__":
    validator = EnvironmentValidator()
    success = validator.run_full_validation()
    sys.exit(0 if success else 1)