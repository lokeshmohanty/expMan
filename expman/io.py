from pathlib import Path
from typing import Any, Dict, List, Optional, Union
import yaml
import polars as pl
try:
    import torch
except ImportError:
    torch = None

import matplotlib.figure
import datetime

# --- Path Management ---

def get_experiment_dir(base_path: Union[str, Path], experiment_name: str) -> Path:
    """Returns the directory path for an experiment."""
    return Path(base_path) / experiment_name

def format_duration(seconds: float) -> str:
    """Formats duration in seconds to a human readable string."""
    hours, remainder = divmod(seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    if hours > 0:
        return f"{int(hours)}h {int(minutes)}m"
    elif minutes > 0:
        return f"{int(minutes)}m {int(seconds)}s"
    else:
        return f"{int(seconds)}s"

def get_run_dir(experiment_dir: Path, run_name: Optional[str] = None) -> Path:
    """Returns the directory path for a specific run. If run_name is None, generates one based on timestamp."""
    if run_name is None:
        run_name = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    return experiment_dir / "runs" / run_name

def ensure_dir(path: Path) -> Path:
    """Ensures a directory exists."""
    path.mkdir(parents=True, exist_ok=True)
    return path

# --- Data I/O ---

def save_yaml(path: Path, data: Dict[str, Any]) -> None:
    """Saves a dictionary to a YAML file."""
    with open(path, 'w') as f:
        yaml.dump(data, f, default_flow_style=False)

def load_yaml(path: Path) -> Dict[str, Any]:
    """Loads a dictionary from a YAML file."""
    if not path.exists():
        return {}
    with open(path, 'r') as f:
        return yaml.safe_load(f) or {}

def save_metrics(path: Path, metrics: List[Dict[str, Any]]) -> None:
    """Saves a list of metrics dictionaries to a parquet file using Polars."""
    if not metrics:
        return
    df = pl.DataFrame(metrics)
    # If file exists, we might want to append, but parquet is immutable.
    # For simplicity in this functional design, we overwrite or expect the caller to manage state.
    # However, for a logger, appending is common. 
    # Efficient parquet appending is tricky. 
    # Strategy: Read existing, concat, write back (simple but slower as size grows).
    # Or write separate chunks and merge later.
    # Let's go with read-concat-write for simplicity as requested.
    
    if path.exists():
        try:
            existing_df = pl.read_parquet(path)
            # Align schemas if needed (handling new columns with nulls)
            # Polars concat requires same schema or diagonal concat
            df = pl.concat([existing_df, df], how="diagonal")
        except Exception:
            # If read fails (corrupt or empty), just overwrite/write new
            pass
            
    df.write_parquet(path)

def load_metrics(path: Path) -> pl.DataFrame:
    """Loads metrics from a parquet file."""
    if not path.exists():
        return pl.DataFrame()
    return pl.read_parquet(path)

def save_model(path: Path, model: Any) -> None:
    """Saves a PyTorch model's state_dict."""
    if torch is None:
        raise ImportError("Torch is not installed. Cannot save model.")
    torch.save(model.state_dict(), path)

def load_model(path: Path, model: Any, map_location: str = 'cpu') -> Any:
    """Loads a PyTorch model's state_dict."""
    if torch is None:
        raise ImportError("Torch is not installed. Cannot load model.")
    state_dict = torch.load(path, map_location=map_location)
    model.load_state_dict(state_dict)
    return model

def save_model_graph(path: Path, model: Any, input_size: tuple) -> None:
    """Generates and saves a model architecture graph as SVG using torchview."""
    try:
        from torchview import draw_graph
    except ImportError:
        # If torch is missing, this will fail too usually, but separating checks is good
        raise ImportError("torchview is not installed. Cannot save model graph.")

    graph = draw_graph(model, input_size=input_size, graph_name="Model Architecture", roll=True)
    # torchview save_graph saves to a file but requires graphviz installed
    # It might save as .gv and .svg. Let's force it to just give us the svg content or save properly.
    # draw_graph returns a graph object.
    # graph.visual_graph is a graphviz Digraph.
    # We can use .render or .pipe
    
    # Using pipe to get bytes and write manually is safer for path control
    svg_bytes = graph.visual_graph.pipe(format='svg')
    with open(path, 'wb') as f:
        f.write(svg_bytes)

def save_plot(path: Path, fig: matplotlib.figure.Figure) -> None:
    """Saves a matplotlib figure."""
    fig.savefig(path)

# --- Analysis Utils ---

def list_experiments(base_path: Path) -> List[Dict[str, str]]:
    """Lists all experiments in the base path with metadata."""
    if not base_path.exists():
        return []
    
    experiments = []
    for p in base_path.iterdir():
        if p.is_dir():
            # Load metadata for display name
            meta = load_experiment_metadata(p)
            experiments.append({
                "id": p.name,
                "display_name": meta.get("display_name") or p.name
            })
    return experiments

def list_runs(experiment_path: Path) -> List[str]:
    """Lists all run names in an experiment."""
    runs_dir = experiment_path / "runs"
    if not runs_dir.exists():
        return []
    return [p.name for p in runs_dir.iterdir() if p.is_dir()]

def get_run_info(run_path: Path) -> Dict[str, Any]:
    """Returns metadata about a run (creation time, etc)."""
    if not run_path.exists():
        return {}
    
    # Try to get creation time from directory
    stat = run_path.stat()
    created = datetime.datetime.fromtimestamp(stat.st_ctime).isoformat()
    
    return {
        "created": created,
        "name": run_path.name
    }

def get_experiment_metadata_path(experiment_dir: Path) -> Path:
    return experiment_dir / "experiment.yaml"

def load_experiment_metadata(experiment_dir: Path) -> Dict[str, Any]:
    return load_yaml(get_experiment_metadata_path(experiment_dir))

def save_experiment_metadata(experiment_dir: Path, metadata: Dict[str, Any]) -> None:
    save_yaml(get_experiment_metadata_path(experiment_dir), metadata)

def get_run_metadata_path(run_dir: Path) -> Path:
    return run_dir / "run.yaml"

def load_run_metadata(run_dir: Path) -> Dict[str, Any]:
    return load_yaml(get_run_metadata_path(run_dir))

def save_run_metadata(run_dir: Path, metadata: Dict[str, Any]) -> None:
    save_yaml(get_run_metadata_path(run_dir), metadata)

