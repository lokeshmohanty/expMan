import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
import yaml
import polars as pl
import torch
import matplotlib.figure
import datetime

# --- Path Management ---

def get_experiment_dir(base_path: Union[str, Path], experiment_name: str) -> Path:
    """Returns the directory path for an experiment."""
    return Path(base_path) / experiment_name

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

def save_model(path: Path, model: torch.nn.Module) -> None:
    """Saves a PyTorch model's state_dict."""
    torch.save(model.state_dict(), path)

def load_model(path: Path, model: torch.nn.Module, map_location: str = 'cpu') -> torch.nn.Module:
    """Loads a PyTorch model's state_dict."""
    state_dict = torch.load(path, map_location=map_location)
    model.load_state_dict(state_dict)
    return model

def save_model_graph(path: Path, model: torch.nn.Module, input_size: tuple) -> None:
    """Generates and saves a model architecture graph as SVG using torchview."""
    from torchview import draw_graph
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

def list_experiments(base_path: Path) -> List[str]:
    """Lists all experiment names in the base path."""
    if not base_path.exists():
        return []
    return [p.name for p in base_path.iterdir() if p.is_dir()]

def list_runs(experiment_path: Path) -> List[str]:
    """Lists all run names in an experiment."""
    runs_dir = experiment_path / "runs"
    if not runs_dir.exists():
        return []
    return [p.name for p in runs_dir.iterdir() if p.is_dir()]
