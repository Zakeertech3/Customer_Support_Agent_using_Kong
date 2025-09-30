import subprocess
import sys
import os

def run_streamlit():
    try:
        cmd = [
            sys.executable, "-m", "streamlit", "run", "streamlit_app.py",
            "--server.port", "8501",
            "--server.address", "0.0.0.0",
            "--browser.gatherUsageStats", "false"
        ]
        
        print("Starting Streamlit frontend on http://localhost:8501")
        print("Make sure the FastAPI backend is running on http://localhost:8080")
        print("Press Ctrl+C to stop the frontend")
        
        subprocess.run(cmd, check=True)
        
    except KeyboardInterrupt:
        print("\nShutting down Streamlit frontend...")
    except subprocess.CalledProcessError as e:
        print(f"Error running Streamlit: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    run_streamlit()