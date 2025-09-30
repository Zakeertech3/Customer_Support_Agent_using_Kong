import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
project_root = Path(__file__).parent.parent
env_file = project_root / ".env"

print(f"Project root: {project_root}")
print(f"Env file path: {env_file}")
print(f"Env file exists: {env_file.exists()}")

# Load the .env file
load_dotenv(env_file)

# Check key environment variables
env_vars_to_check = [
    "GROQ_API_KEY",
    "KONG_ADMIN_URL", 
    "KONG_PROXY_URL",
    "CHROMADB_URL"
]

print("\nEnvironment Variables:")
print("-" * 30)

for var in env_vars_to_check:
    value = os.getenv(var)
    if value:
        # Mask API key for security
        if "API_KEY" in var:
            masked_value = value[:8] + "..." + value[-4:] if len(value) > 12 else "***"
            print(f"{var}: {masked_value}")
        else:
            print(f"{var}: {value}")
    else:
        print(f"{var}: NOT SET")

# Test config import
print("\nTesting config import...")
try:
    import sys
    sys.path.insert(0, str(project_root))
    
    from app.config import config
    print("✓ Config imported successfully")
    print(f"✓ Groq API key set: {'Yes' if config.groq.api_key else 'No'}")
    print(f"✓ Kong Admin URL: {config.kong.admin_url}")
    print(f"✓ ChromaDB URL: {config.chromadb.url}")
    
except Exception as e:
    print(f"✗ Config import failed: {e}")
