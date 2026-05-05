"""
gRPC Agent Server 启动脚本 - ShuaiTravelAgent Agent Service
"""
import sys
import os

# Set project root
project_root = os.path.dirname(os.path.abspath(__file__))
os.chdir(project_root)

# Add agent/ to path so relative imports work
agent_path = os.path.join(project_root, 'agent')
if agent_path not in sys.path:
    sys.path.insert(0, agent_path)

try:
    from src.server import serve
    from src.config.config_manager import ConfigManager
except ImportError as e:
    print("\n[X] Import Error: " + str(e))
    print("\nPlease run from project root: " + project_root)
    print("Python path: " + str(sys.path) + "\n")
    sys.exit(1)

if __name__ == "__main__":
    try:
        # Use the new YAML config file
        config_path = os.path.join(project_root, 'config', 'llm_config.yaml')
        config_manager = ConfigManager(config_path)

        # Get port from config or use default
        port = config_manager.grpc_config.get('port', 50051)

        print("\n[*] Starting Agent gRPC Service...")
        print("   Config: " + config_path)
        print("   Port: " + str(port))
        print("   Default Model: " + config_manager.get_default_model_id())
        print()

        server = serve(config_path=config_path, port=port)
        print("\n[OK] Agent gRPC Service started on port " + str(port))
        print("   Press Ctrl+C to stop\n")
        server.wait_for_termination()
    except FileNotFoundError as e:
        print("\n[X] Configuration Error:\n" + str(e) + "\n")
        sys.exit(1)
    except Exception as e:
        print("\n[X] Startup Error: " + str(e) + "\n")
        sys.exit(1)
