import argparse
import sys
from pathlib import Path
import code
import uvicorn
from expman.analysis import ExperimentAnalyzer
from expman.web import app
from expman import io as utils
import subprocess
import time
import os
import signal
import threading

def dev_command(args):
    """Starts the development server with frontend watch."""
    # Locate frontend dir relative to this file
    package_dir = Path(__file__).parent
    frontend_dir = package_dir / "frontend"
    
    if not frontend_dir.exists():
        print(f"Error: Frontend directory not found at {frontend_dir}")
        return

    # Frontend Process
    print("[dev] Launching Frontend Watch...")
    try:
        frontend_proc = subprocess.Popen(
            ["npm", "run", "build", "--", "--watch"], 
            cwd=str(frontend_dir),
            shell=False 
        )
    except FileNotFoundError:
        print("Error: npm not found. Is node installed?")
        return

    # Backend Process
    print("[dev] Launching Backend Server...")
    # We use uvicorn with reload for backend dev
    # python -m expman.web (but simpler: direct uvicorn arg?)
    # If we run as module, we get reliable imports.
    # Note: expman.web:app is the target.
    # Using sys.executable to ensure same env.
    
    env = os.environ.copy()
    env["PYTHONPATH"] = str(package_dir.parent) # Ensure we can import expman from source if working locally
    
    backend_cmd = [sys.executable, "-m", "uvicorn", "expman.web:app", "--reload", "--host", args.host, "--port", str(args.port)]
    if args.experiments_dir:
         # Pass args? uvicorn can't easily pass args to app unless factory. 
         # But expman.web uses global analyzer initialized by side effect or defaults.
         # expman.web main() does arg parsing!
         # If we run uvicorn expman.web:app, main() is NOT called.
         # So analyzer uses default 'experiments' dir in web.py.
         # If user wants custom dir, we need to handle that.
         # 
         # Solution: expman.web uses global 'analyzer'. 
         # In reload mode, uvicorn imports the module fresh. 
         # We need a way to configure it. Environment variable?
         env["EXPMAN_BASE_DIR"] = args.experiments_dir

    backend_proc = subprocess.Popen(
        backend_cmd,
        cwd=str(package_dir.parent),
        env=env,
        shell=False
    )

    print("[dev] Both processes started. Press Ctrl+C to stop.")

    try:
        while True:
            if frontend_proc.poll() is not None:
                print("[dev] Frontend exited unexpectedly.")
                break
            if backend_proc.poll() is not None:
                print("[dev] Backend exited unexpectedly.")
                break
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\n[dev] Stopping processes...")
    finally:
        if frontend_proc.poll() is None:
            frontend_proc.terminate()
        if backend_proc.poll() is None:
            backend_proc.terminate()
            
    print("[dev] Done.")

def serve_command(args):
    """Starts the ExpMan server."""
    host = args.host
    port = args.port
    experiments_dir = args.experiments_dir
    
    # We need to tell the server app where to look.
    # Since 'app' is global in server.py and initialized there, 
    # and ExperimentAnalyzer is also global there.
    # We can inject dependencies or set global state.
    # server.py's 'analyzer' is global.
    
    from expman import web as server
    server.analyzer = ExperimentAnalyzer(base_dir=experiments_dir)
    
    print(f"Starting ExpMan UI at http://{host}:{port}")
    print(f"Serving experiments from: {experiments_dir}")
    
    uvicorn.run(app, host=host, port=port)

def load_command(args):
    """Loads a run into an interactive shell."""
    run_dir = Path(args.run_dir).resolve()
    if not run_dir.exists():
        print(f"Error: Run directory not found: {run_dir}")
        sys.exit(1)
        
    print(f"Loading run from: {run_dir}")
    
    # Analyze structure
    metrics_path = run_dir / "metrics.parquet"
    config_path = run_dir / "config.yaml"
    
    variables = {}
    
    if metrics_path.exists():
        print("Loading metrics...")
        variables['metrics'] = utils.load_metrics(metrics_path)
        print(" -> 'metrics' (Polars DataFrame)")
    else:
        print("! No metrics.parquet found.")
        
    if config_path.exists():
        print("Loading config...")
        variables['config'] = utils.load_yaml(config_path)
        print(" -> 'config' (Dict)")
    else:
        print("! No config.yaml found.")
        
    variables['run_dir'] = run_dir
    variables['utils'] = utils
    
    banner = f"""
ExpMan Interactive Shell
------------------------
Loaded Run: {run_dir.name}
Variables available: {', '.join(variables.keys())}
    """
    
    code.interact(banner=banner, local=variables)

def main():
    parser = argparse.ArgumentParser(description="ExpMan CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)
    
    # serve command
    serve_parser = subparsers.add_parser("serve", help="Start the web UI server")
    serve_parser.add_argument("experiments_dir", nargs="?", default="./experiments", help="Path to experiments directory")
    serve_parser.add_argument("--host", default="127.0.0.1", help="Host to bind to")
    serve_parser.add_argument("--port", type=int, default=8000, help="Port to bind to")
    
    # load command
    load_parser = subparsers.add_parser("load", help="Load a run into interactive python shell")
    load_parser.add_argument("run_dir", help="Path to the specific run directory")

    # dev command
    dev_parser = subparsers.add_parser("dev", help="Start development mode (frontend watch + backend reload)")
    dev_parser.add_argument("--host", default="127.0.0.1", help="Host to bind to")
    dev_parser.add_argument("--port", type=int, default=8000, help="Port to bind to")
    dev_parser.add_argument("--experiments-dir", default="./experiments", help="Path to experiments directory")
    
    args = parser.parse_args()
    
    if args.command == "serve":
        serve_command(args)
    elif args.command == "load":
        load_command(args)
    elif args.command == "dev":
        dev_command(args)

if __name__ == "__main__":
    main()
