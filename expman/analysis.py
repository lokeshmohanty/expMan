from pathlib import Path
from typing import Any, Dict, List, Optional
import datetime
import polars as pl


from expman import io as utils

class ExperimentAnalyzer:
    """
    Class to analyze and visualize experiment results.
    """
    def __init__(self, base_dir: str = "experiments"):
        self.base_dir = Path(base_dir)
        self.live_mode = True

    def get_experiments(self) -> List[Dict[str, str]]:
        return utils.list_experiments(self.base_dir)

    def get_runs(self, experiment_name: str) -> List[str]:
        experiment_path = utils.get_experiment_dir(self.base_dir, experiment_name)
        return utils.list_runs(experiment_path)

    def get_run_metrics(self, experiment_name: str, run_name: str, since_step: Optional[int] = None) -> pl.DataFrame:
        run_path = utils.get_run_dir(utils.get_experiment_dir(self.base_dir, experiment_name), run_name)
        df = utils.load_metrics(run_path / "metrics.parquet")
        
        if since_step is not None and not df.is_empty() and 'step' in df.columns:
            df = df.filter(pl.col('step') > since_step)
            
        return df

    def get_run_config(self, experiment_name: str, run_name: str) -> Dict[str, Any]:
        run_path = utils.get_run_dir(utils.get_experiment_dir(self.base_dir, experiment_name), run_name)
        return utils.load_yaml(run_path / "config.yaml")





    def get_experiment_stats(self, experiment_name: str) -> List[Dict[str, Any]]:
        """
        Returns specific stats for all runs in an experiment for the summary view.
        """
        runs = self.get_runs(experiment_name)
        stats = []
        experiment_path = utils.get_experiment_dir(self.base_dir, experiment_name)
        
        for run in runs:
            run_path = utils.get_run_dir(experiment_path, run)
            info = utils.get_run_info(run_path)
            
            # Get last metrics if available
            df = self.get_run_metrics(experiment_name, run)
            last_metrics = {}
            duration = "-"
            
            if not df.is_empty():
                # Take the last row as dict
                row = df.tail(1).to_dicts()[0]
                last_metrics = row
                
                # Check for explicit duration metric (logged by close())
                if "duration" in last_metrics:
                     d_sec = last_metrics["duration"]
                     duration = utils.format_duration(d_sec)
                elif "timestamp" in df.columns:
                     # Attempt to calculate ongoing duration
                     try:
                         # Ensure we have a valid creation time
                         if info.get("created"):
                             created_dt = datetime.datetime.fromisoformat(info.get("created"))
                             # Use current time for ongoing
                             now = datetime.datetime.now()
                             diff = (now - created_dt).total_seconds()
                             if diff > 0:
                                 duration = f"Ongoing ({utils.format_duration(diff)})"
                     except Exception:
                         pass

            # Merge last_metrics first, then overwrite duration with formatted string
            entry = {
                "run": run,
                "created": info.get("created"),
                **last_metrics
            }
            entry["duration"] = duration
            stats.append(entry)
        
        # Sort by creation time desc (if available) or name
        stats.sort(key=lambda x: x.get("created", ""), reverse=True)
        return stats

