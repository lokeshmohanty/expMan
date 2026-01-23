import argparse
import sys
from pathlib import Path
import code
import uvicorn
from .analyzer import ExperimentAnalyzer
from .server import app
from . import utils

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
    
    from . import server
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
    
    args = parser.parse_args()
    
    if args.command == "serve":
        serve_command(args)
    elif args.command == "load":
        load_command(args)

if __name__ == "__main__":
    main()
