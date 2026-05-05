"""
FastAPI启动脚本 - ShuaiTravelAgent Web API Server
"""
import sys
import os
import subprocess

# Set project root
project_root = os.path.dirname(os.path.abspath(__file__))
web_path = os.path.join(project_root, 'web')

if __name__ == "__main__":
    # Run directly from web directory
    cmd = [
        sys.executable, "-m", "uvicorn", "src.main:app",
        "--host", "0.0.0.0",
        "--port", "8000"
    ]

    print("[*] Starting Web API Server...")
    print(f"    Working directory: {web_path}")

    env = os.environ.copy()
    subprocess.run(cmd, cwd=web_path, env=env)
