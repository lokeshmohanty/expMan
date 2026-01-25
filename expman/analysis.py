from pathlib import Path
from typing import Any, Dict, List, Optional
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
                
                # Calculate duration
                # Strategy: 
                # 1. If 'timestamp' exists in metrics (absolute time), duration = last_timestamp - created_time
                # 2. If 'relative_time' or similar exists, use that.
                # 3. If 'step', checking duration per step is hard.
                # Let's try to parse creation time and compare with last timestamp if available.
                import datetime
                try:
                    created_dt = datetime.datetime.fromisoformat(info.get("created"))
                    # If metrics have a timestamp column (assumed float seconds or iso string?)
                    # If it's not standard, we might skip. 
                    # For now simpliest is: if we have metrics, do we have a 'timestamp' column?
                    # Usually metrics logger adds 'timestamp'.
                    if "timestamp" in df.columns:
                        # Assuming timestamp is seconds since epoch float (common in ML loggers)
                        last_ts = df["timestamp"][-1]
                        # If timestamp is very large, it's epoch. If small, it's relative?
                        # Let's assume epoch for now if > 1e9
                        if last_ts > 1e9: 
                           start_ts = created_dt.timestamp()
                           diff = last_ts - start_ts
                           if diff > 0:
                               # Format duration
                               hours, remainder = divmod(diff, 3600)
                               minutes, seconds = divmod(remainder, 60)
                               if hours > 0:
                                   duration = f"{int(hours)}h {int(minutes)}m"
                               elif minutes > 0:
                                   duration = f"{int(minutes)}m {int(seconds)}s"
                               else:
                                    duration = f"{int(seconds)}s"
                except Exception:
                    pass

            stats.append({
                "run": run,
                "created": info.get("created"),
                "duration": duration,
                **last_metrics
            })
        
        # Sort by creation time desc (if available) or name
        stats.sort(key=lambda x: x.get("created", ""), reverse=True)
        return stats

