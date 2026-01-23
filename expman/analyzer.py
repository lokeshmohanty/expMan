from pathlib import Path
from typing import Any, Dict, List, Optional
import polars as pl
import matplotlib.pyplot as plt

from . import utils

class ExperimentAnalyzer:
    """
    Class to analyze and visualize experiment results.
    """
    def __init__(self, base_dir: str = "experiments"):
        self.base_dir = Path(base_dir)

    def get_experiments(self) -> List[str]:
        return utils.list_experiments(self.base_dir)

    def get_runs(self, experiment_name: str) -> List[str]:
        experiment_path = utils.get_experiment_dir(self.base_dir, experiment_name)
        return utils.list_runs(experiment_path)

    def get_run_metrics(self, experiment_name: str, run_name: str) -> pl.DataFrame:
        run_path = utils.get_run_dir(utils.get_experiment_dir(self.base_dir, experiment_name), run_name)
        return utils.load_metrics(run_path / "metrics.parquet")

    def get_run_config(self, experiment_name: str, run_name: str) -> Dict[str, Any]:
        run_path = utils.get_run_dir(utils.get_experiment_dir(self.base_dir, experiment_name), run_name)
        return utils.load_yaml(run_path / "config.yaml")

    def plot_metric(self, experiment_name: str, metric_name: str, run_names: Optional[List[str]] = None, ax: Optional[plt.Axes] = None):
        """
        Plots a metric over steps for specified runs.
        """
        if run_names is None:
            run_names = self.get_runs(experiment_name)
        
        if ax is None:
            fig, ax = plt.subplots()
        
        for run_name in run_names:
            df = self.get_run_metrics(experiment_name, run_name)
            if metric_name in df.columns:
                # Assuming 'step' exists. If not, use index.
                x = df['step'] if 'step' in df.columns else range(len(df))
                ax.plot(x, df[metric_name], label=run_name)
        
        ax.set_xlabel("Step")
        ax.set_ylabel(metric_name)
        ax.legend()
        return ax

    def get_population_metrics(self, experiment_name: str, metric_name: str) -> Dict[str, float]:
        """
        Computes stats (mean, std, max) for a metric across all runs in an experiment
        (using the last logged value of the metric for each run).
        """
        runs = self.get_runs(experiment_name)
        final_values = []
        for run in runs:
            df = self.get_run_metrics(experiment_name, run)
            if not df.is_empty() and metric_name in df.columns:
                val = df[metric_name][-1] # Last value
                final_values.append(val)
        
        if not final_values:
            return {}
            
        import numpy as np
        return {
            "mean": float(np.mean(final_values)),
            "std": float(np.std(final_values)),
            "max": float(np.max(final_values)),
            "min": float(np.min(final_values))
        }
