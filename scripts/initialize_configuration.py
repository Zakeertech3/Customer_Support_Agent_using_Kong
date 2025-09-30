import os
import sys
import time
import json
import logging
from pathlib import Path
from typing import Dict, Any

sys.path.append(str(Path(__file__).parent.parent))

from app.config import config
from app.services.environment_service import environment_service
from app.services.chromadb_service import chromadb_service
from scripts.deploy_kong_config import deploy_kong_config, validate_kong_config, check_kong_health

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ConfigurationInitializer:
    def __init__(self):
        self.initialization_steps = [
            ("Environment Validation", self.validate_environment),
            ("ChromaDB Initialization", self.initialize_chromadb),
            ("Kong Configuration Deployment", self.deploy_kong_configuration),
            ("Service Health Checks", self.perform_health_checks),
            ("Configuration Summary", self.generate_summary)
        ]
        
        self.results = {}
    
    def run_initialization(self) -> Dict[str, Any]:
        logger.info("Starting Configuration Initialization Process")
        logger.info("=" * 60)
        
        overall_success = True
        
        for step_name, step_function in self.initialization_steps:
            logger.info(f"\nStep: {step_name}")
            logger.info("-" * 40)
            
            try:
                result = step_function()
                self.results[step_name] = result
                
                if result.get("success", False):
                    logger.info(f"✓ {step_name} completed successfully")
                else:
                    logger.error(f"✗ {step_name} failed")
                    overall_success = False
                    
            except Exception as e:
                logger.error(f"✗ {step_name} failed with error: {e}")
                self.results[step_name] = {"success": False, "error": str(e)}
                overall_success = False
        
        self.results["overall_success"] = overall_success
        
        logger.info("\n" + "=" * 60)
        if overall_success:
            logger.info("✓ Configuration initialization completed successfully!")
        else:
            logger.error("✗ Configuration initialization completed with errors!")
        
        return self.results
    
    def validate_environment(self) -> Dict[str, Any]:
        try:
            validation_result = environment_service.validate_environment()
            
            if validation_result["valid"]:
                logger.info("Environment validation passed")
                return {"success": True, "validation": validation_result}
            else:
                logger.warning(f"Missing required variables: {validation_result['missing_required']}")
                return {"success": False, "validation": validation_result}
                
        except Exception as e:
            logger.error(f"Environment validation failed: {e}")
            return {"success": False, "error": str(e)}
    
    def initialize_chromadb(self) -> Dict[str, Any]:
        try:
            logger.info("Initializing ChromaDB connection...")
            
            if chromadb_service.initialize():
                health_status = chromadb_service.health_check()
                logger.info("ChromaDB initialized successfully")
                return {"success": True, "health": health_status}
            else:
                logger.error("ChromaDB initialization failed")
                return {"success": False, "error": "Failed to initialize ChromaDB"}
                
        except Exception as e:
            logger.error(f"ChromaDB initialization error: {e}")
            return {"success": False, "error": str(e)}
    
    def deploy_kong_configuration(self) -> Dict[str, Any]:
        try:
            logger.info("Checking Kong Gateway status...")
            
            if not check_kong_health():
                logger.warning("Kong Gateway is not running")
                return {"success": False, "error": "Kong Gateway not available"}
            
            logger.info("Deploying Kong configuration...")
            
            if deploy_kong_config():
                logger.info("Kong configuration deployed successfully")
                
                time.sleep(2)
                
                if validate_kong_config():
                    logger.info("Kong configuration validation passed")
                    return {"success": True, "deployed": True, "validated": True}
                else:
                    logger.warning("Kong configuration validation failed")
                    return {"success": False, "deployed": True, "validated": False}
            else:
                logger.error("Kong configuration deployment failed")
                return {"success": False, "deployed": False}
                
        except Exception as e:
            logger.error(f"Kong configuration deployment error: {e}")
            return {"success": False, "error": str(e)}
    
    def perform_health_checks(self) -> Dict[str, Any]:
        try:
            health_results = {}
            
            logger.info("Performing service health checks...")
            
            health_results["chromadb"] = chromadb_service.health_check()
            health_results["kong"] = {"healthy": check_kong_health()}
            
            environment_config = environment_service.get_service_configurations()
            health_results["configuration"] = {
                "groq_api_key_set": environment_config["groq"]["api_key_set"],
                "database_configured": environment_config["database"]["password_set"],
                "cache_enabled": environment_config["cache"]["enabled"]
            }
            
            all_healthy = all([
                health_results["chromadb"]["status"] == "healthy",
                health_results["kong"]["healthy"],
                health_results["configuration"]["groq_api_key_set"]
            ])
            
            logger.info(f"Health check results: {'All services healthy' if all_healthy else 'Some services have issues'}")
            
            return {"success": all_healthy, "health_results": health_results}
            
        except Exception as e:
            logger.error(f"Health check error: {e}")
            return {"success": False, "error": str(e)}
    
    def generate_summary(self) -> Dict[str, Any]:
        try:
            logger.info("Generating configuration summary...")
            
            summary = environment_service.export_configuration_summary()
            
            summary_file = Path("configuration_summary.json")
            with open(summary_file, 'w') as f:
                json.dump(summary, f, indent=2)
            
            logger.info(f"Configuration summary saved to: {summary_file}")
            
            return {"success": True, "summary_file": str(summary_file), "summary": summary}
            
        except Exception as e:
            logger.error(f"Summary generation error: {e}")
            return {"success": False, "error": str(e)}
    
    def print_initialization_report(self):
        print("\n" + "=" * 80)
        print("CONFIGURATION INITIALIZATION REPORT")
        print("=" * 80)
        
        for step_name, result in self.results.items():
            if step_name == "overall_success":
                continue
                
            status = "✓ PASS" if result.get("success", False) else "✗ FAIL"
            print(f"{step_name:<40} {status}")
            
            if not result.get("success", False) and "error" in result:
                print(f"  Error: {result['error']}")
        
        print("-" * 80)
        overall_status = "✓ SUCCESS" if self.results.get("overall_success", False) else "✗ FAILED"
        print(f"{'Overall Status':<40} {overall_status}")
        print("=" * 80)

def main():
    initializer = ConfigurationInitializer()
    results = initializer.run_initialization()
    
    initializer.print_initialization_report()
    
    if not results.get("overall_success", False):
        sys.exit(1)

if __name__ == "__main__":
    main()
