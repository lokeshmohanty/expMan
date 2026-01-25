from pathlib import Path
from typing import Any, Dict, Optional
from loguru import logger
import matplotlib.figure
import atexit
import datetime
try:
    import torch
except ImportError:
    torch = None

from . import io as utils

class Experiment:
    """
    Manages a single experiment run.
    API designed to be simple and require minimal boilerplate.
    """

    def __init__(
        self, 
        experiment_name: str, 
        run_name: Optional[str] = None, 
        base_dir: str = "experiments",
        auto_create: bool = True
    ):
        self.base_dir = Path(base_dir)
        self.experiment_name = experiment_name
        self.experiment_dir = utils.ensure_dir(utils.get_experiment_dir(self.base_dir, experiment_name))
        
        self.run_dir = utils.ensure_dir(utils.get_run_dir(self.experiment_dir, run_name))
        self.run_name = self.run_dir.name
        
        self.metrics_buffer = []
        self.metrics_file = self.run_dir / "metrics.parquet"
        self.config_file = self.run_dir / "config.yaml"
        self.params_file = self.run_dir / "params.yaml" # Separating generic config vs model hyperparams if needed, but keeping simple for now.

        # Setup Logging
        self._setup_logger()
        self.logger.info(f"Initialized experiment: {self.experiment_name} / {self.run_name}")
        
        self.start_time = datetime.datetime.now()
        self.is_closed = False
        atexit.register(self.close)

    def _setup_logger(self):
        """Configures loguru to log to a file in the run directory."""
        log_file = self.run_dir / "run.log"
        # We want a fresh logger config for this instance or global?
        # Loguru is global. We add a sink with a filter for this specific run if we wanted concurrent runs in same process,
        # but typically runs are 1 per process. Let's just add a sink.
        logger.add(log_file, level="INFO")
        self.logger = logger

    def log_params(self, params: Dict[str, Any]):
        """Logs hyperparameters/configuration."""
        existing = utils.load_yaml(self.config_file)
        existing.update(params)
        utils.save_yaml(self.config_file, existing)
        self.logger.info(f"Logged params: {params}")

    def log_metrics(self, metrics: Dict[str, Any], step: Optional[int] = None):
        """
        Logs a dictionary of metrics.
        If step is not provided, it's auto-incremented based on call count (naive) or just logged as is.
        Better to force step or generic 'timestamp'.
        """
        if step is not None:
            metrics['step'] = step
        
        # Add timestamp
        import datetime
        metrics['timestamp'] = datetime.datetime.now().isoformat()
        
        self.metrics_buffer.append(metrics)
        
        # Flush periodically (here, every log for simplicity/safety, or can batch)
        # For this requirement: "track... metrics", lets just write immediately to ensure persistence
        utils.save_metrics(self.metrics_file, [metrics])
        self.metrics_buffer = [] # Clear after write

    def save_model(self, model: Any, filename: str = "model.pt", input_size: Optional[tuple] = None):
        """
        Saves a pytorch model asynchronously.
        
        Args:
            model: The PyTorch model to save.
            filename: The filename for the saved model (e.g., 'model.pt').
            input_size: Optional input size tuple (e.g., (1, 3, 224, 224)). 
                        If provided, an SVG graph of the model is also generated and saved.
        """
        if torch is None:
            self.logger.warning("Torch is not installed. Skipping model save.")
            return
        import threading
        import copy
        
        # We need to copy the state dict or model if we want true safety during training,
        # but deepcopying a model can be heavy.
        # For state_dict saving, we usually just need the state dict.
        # However, for graph generation we need the model structure.
        # If the user continues training while we save, weights change.
        # Let's clone the state_dict for saving weights safely.
        # Graph generation operates on structure, so concurrent weight updates shouldn't crash it,
        # usually.
        
        state_dict = {k: v.cpu() for k, v in model.state_dict().items()}
        
        # Define the task
        def _save_task():
            path = self.run_dir / filename
            try:
                # Save weights locally
                torch.save(state_dict, path)
                self.logger.info(f"Saved model to {path}")
                
                # Generate Graph if input_size is provided
                if input_size:
                    svg_filename = Path(filename).stem + ".svg"
                    svg_path = self.run_dir / svg_filename
                    try:
                        utils.save_model_graph(svg_path, model, input_size)
                        self.logger.info(f"Saved model graph to {svg_path}")
                    except Exception as e:
                        self.logger.error(f"Failed to generate model graph: {e}. Check graphviz installation.")
                        
            except Exception as e:
                self.logger.error(f"Failed to save model: {e}")

        # Start thread
        t = threading.Thread(target=_save_task)
        t.start()

    def save_plot(self, fig: matplotlib.figure.Figure, filename: str):
        """Saves a plot."""
        if not filename.endswith('.png'):
            filename += '.png'
        path = self.run_dir / filename
        utils.save_plot(path, fig)
        self.logger.info(f"Saved plot to {path}")

    def info(self, msg: str):
        self.logger.info(msg)

    def close(self):
        """
        Gracefully closes the experiment.
        Logs duration and status, flushes metrics.
        Called automatically via atexit.
        """
        if self.is_closed:
            return
            
        end_time = datetime.datetime.now()
        duration = (end_time - self.start_time).total_seconds()
        
        self.logger.info(f"Run finished. Duration: {duration:.2f}s")
        
        # Log final status metric
        final_metric = {
            "status": "FINISHED",
            "duration": duration,
            "finished_at": end_time.isoformat()
        }
        
        # We append to buffer and then forced flush
        self.metrics_buffer.append(final_metric)
        utils.save_metrics(self.metrics_file, self.metrics_buffer)
        self.metrics_buffer = [] # Clear
        
        self.is_closed = True
