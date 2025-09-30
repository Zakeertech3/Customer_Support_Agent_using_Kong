import os
import sys
import json
import requests
import time
from pathlib import Path
from typing import Dict, Any, List

sys.path.append(str(Path(__file__).parent.parent))

from app.config import config
from app.services.environment_service import environment_service
from app.services.chromadb_service import chromadb_service

class CompleteSetupValidator:
    def __init__(self):
        self.validation_results = {}
        
    def validate_all_components(self) -> Dict[str, Any]:
        print("Kong Support Agent - Complete Setup Validation")
        print("=" * 60)
        
        validation_steps = [
            ("Environment Configuration", self.validate_environment_config),
            ("Kong Gateway Services", self.validate_kong_services),
            ("ChromaDB Connection", self.validate_chromadb_connection),
            ("Groq API Authentication", self.validate_groq_authentication),
            ("Plugin Configurations", self.validate_plugin_configurations),
            ("Service Routing", self.validate_service_routing),
            ("Cache Functionality", self.validate_cache_functionality)
        ]
        
        overall_success = True
        
        for step_name, validation_function in validation_steps:
            print(f"\n{step_name}:")
            print("-" * 40)
            
            try:
                result = validation_function()
                self.validation_results[step_name] = result
                
                if result.get("success", False):
                    print(f"✓ {step_name} - PASSED")
                else:
                    print(f"✗ {step_name} - FAILED")
                    if "error" in result:
                        print(f"  Error: {result['error']}")
                    overall_success = False
                    
            except Exception as e:
                print(f"✗ {step_name} - ERROR: {e}")
                self.validation_results[step_name] = {"success": False, "error": str(e)}
                overall_success = False
        
        self.validation_results["overall_success"] = overall_success
        return self.validation_results
    
    def validate_environment_config(self) -> Dict[str, Any]:
        try:
            validation = environment_service.validate_environment()
            
            if validation["valid"]:
                config_summary = environment_service.get_service_configurations()
                return {
                    "success": True,
                    "validation": validation,
                    "configurations": config_summary
                }
            else:
                return {
                    "success": False,
                    "validation": validation,
                    "error": f"Missing required variables: {validation['missing_required']}"
                }
                
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def validate_kong_services(self) -> Dict[str, Any]:
        try:
            admin_url = config.kong.admin_url
            
            services_response = requests.get(f"{admin_url}/services", timeout=10)
            routes_response = requests.get(f"{admin_url}/routes", timeout=10)
            
            if services_response.status_code == 200 and routes_response.status_code == 200:
                services = services_response.json()["data"]
                routes = routes_response.json()["data"]
                
                expected_services = ["groq-simple-service", "groq-complex-service", "groq-fallback-service", "groq-unified-service"]
                configured_services = [s["name"] for s in services]
                
                missing_services = set(expected_services) - set(configured_services)
                
                if not missing_services:
                    return {
                        "success": True,
                        "services_count": len(services),
                        "routes_count": len(routes),
                        "services": configured_services
                    }
                else:
                    return {
                        "success": False,
                        "error": f"Missing services: {missing_services}",
                        "configured_services": configured_services
                    }
            else:
                return {
                    "success": False,
                    "error": f"Kong API not accessible: {services_response.status_code}"
                }
                
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def validate_chromadb_connection(self) -> Dict[str, Any]:
        try:
            if not chromadb_service.is_connected:
                chromadb_service.initialize()
            
            health_status = chromadb_service.health_check()
            
            if health_status["status"] == "healthy":
                return {
                    "success": True,
                    "health_status": health_status
                }
            else:
                return {
                    "success": False,
                    "error": "ChromaDB not healthy",
                    "health_status": health_status
                }
                
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def validate_groq_authentication(self) -> Dict[str, Any]:
        try:
            if not config.groq.api_key:
                return {"success": False, "error": "GROQ_API_KEY not set"}
            
            headers = {
                "Authorization": f"Bearer {config.groq.api_key}",
                "Content-Type": "application/json"
            }
            
            test_payload = {
                "messages": [{"role": "user", "content": "test"}],
                "model": config.groq.simple_model,
                "max_tokens": 10
            }
            
            response = requests.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers=headers,
                json=test_payload,
                timeout=30
            )
            
            if response.status_code == 200:
                return {
                    "success": True,
                    "api_key_valid": True,
                    "model_accessible": config.groq.simple_model
                }
            else:
                return {
                    "success": False,
                    "error": f"Groq API authentication failed: {response.status_code}",
                    "response": response.text[:200]
                }
                
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def validate_plugin_configurations(self) -> Dict[str, Any]:
        try:
            admin_url = config.kong.admin_url
            
            plugins_response = requests.get(f"{admin_url}/plugins", timeout=10)
            
            if plugins_response.status_code == 200:
                plugins = plugins_response.json()["data"]
                
                expected_plugins = [
                    "ai-proxy-advanced",
                    "ai-semantic-cache", 
                    "ai-prompt-guard",
                    "ai-rate-limiting-advanced"
                ]
                
                configured_plugins = [p["name"] for p in plugins]
                plugin_counts = {}
                
                for plugin_name in expected_plugins:
                    count = configured_plugins.count(plugin_name)
                    plugin_counts[plugin_name] = count
                
                all_configured = all(count > 0 for count in plugin_counts.values())
                
                return {
                    "success": all_configured,
                    "plugin_counts": plugin_counts,
                    "total_plugins": len(plugins)
                }
            else:
                return {
                    "success": False,
                    "error": f"Failed to retrieve plugins: {plugins_response.status_code}"
                }
                
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def validate_service_routing(self) -> Dict[str, Any]:
        try:
            proxy_url = config.kong.proxy_url
            
            routes_to_test = [
                "/ai/simple",
                "/ai/complex", 
                "/ai/fallback",
                "/ai/chat"
            ]
            
            routing_results = {}
            
            for route in routes_to_test:
                try:
                    response = requests.get(f"{proxy_url}{route}", timeout=5)
                    routing_results[route] = {
                        "accessible": True,
                        "status_code": response.status_code
                    }
                except Exception as e:
                    routing_results[route] = {
                        "accessible": False,
                        "error": str(e)
                    }
            
            all_accessible = all(result["accessible"] for result in routing_results.values())
            
            return {
                "success": all_accessible,
                "routing_results": routing_results
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def validate_cache_functionality(self) -> Dict[str, Any]:
        try:
            if not chromadb_service.is_connected:
                return {"success": False, "error": "ChromaDB not connected"}
            
            test_collection = config.chromadb.simple_collection
            test_query = "test cache query"
            test_response = "test cache response"
            
            cache_add_success = chromadb_service.add_to_cache(
                test_collection, 
                test_query, 
                test_response,
                {"timestamp": str(time.time()), "model": "test"}
            )
            
            if cache_add_success:
                cached_result = chromadb_service.search_cache(test_collection, test_query)
                
                if cached_result and cached_result["response"] == test_response:
                    return {
                        "success": True,
                        "cache_add": True,
                        "cache_retrieve": True,
                        "similarity": cached_result["similarity"]
                    }
                else:
                    return {
                        "success": False,
                        "cache_add": True,
                        "cache_retrieve": False,
                        "error": "Failed to retrieve cached data"
                    }
            else:
                return {
                    "success": False,
                    "cache_add": False,
                    "error": "Failed to add data to cache"
                }
                
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def generate_validation_report(self) -> str:
        report = []
        report.append("KONG SUPPORT AGENT - SETUP VALIDATION REPORT")
        report.append("=" * 60)
        report.append("")
        
        for component, result in self.validation_results.items():
            if component == "overall_success":
                continue
                
            status = "✓ PASS" if result.get("success", False) else "✗ FAIL"
            report.append(f"{component:<35} {status}")
            
            if not result.get("success", False) and "error" in result:
                report.append(f"  Error: {result['error']}")
        
        report.append("")
        report.append("-" * 60)
        overall_status = "✓ ALL SYSTEMS OPERATIONAL" if self.validation_results.get("overall_success", False) else "✗ SETUP INCOMPLETE"
        report.append(f"Overall Status: {overall_status}")
        report.append("=" * 60)
        
        return "\n".join(report)
    
    def save_validation_results(self, filename: str = "validation_results.json"):
        with open(filename, 'w') as f:
            json.dump(self.validation_results, f, indent=2)
        print(f"Validation results saved to: {filename}")

def main():
    validator = CompleteSetupValidator()
    
    print("Starting complete setup validation...")
    print("This may take a few minutes...\n")
    
    results = validator.validate_all_components()
    
    print("\n" + "=" * 60)
    print(validator.generate_validation_report())
    
    validator.save_validation_results()
    
    if results.get("overall_success", False):
        print("\n🎉 Congratulations! Your Kong Support Agent setup is complete and operational.")
        print("You can now start using the application:")
        print("  Backend:  python main.py")
        print("  Frontend: streamlit run streamlit_app.py")
    else:
        print("\n⚠️  Setup validation failed. Please address the issues above.")
        sys.exit(1)

if __name__ == "__main__":
    main()
