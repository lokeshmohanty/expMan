import shutil
import time
import math
import random
from expman import Experiment

def main():
    shutil.rmtree("experiments/live_test_experiment", ignore_errors=True)
    exp = Experiment("live_test_experiment", run_name="run_001")
    exp.log_params({"lr": 0.01, "optimizer": "adam"})

    exp.info(f"Starting live experiment: {exp.experiment_name}/{exp.run_name}")
    exp.info("Logging metrics... (Press Ctrl+C to stop)")

    try:
        for i in range(1000):
            # Simulate training work
            time.sleep(0.5)
            
            # Generate some interesting simulated curves
            loss = 2.0 * math.exp(-i / 100.0) + random.random() * 0.1
            accuracy = 1.0 - math.exp(-i / 200.0) + random.random() * 0.05
            
            metrics = {
                "loss": loss,
                "accuracy": accuracy,
                "val_loss": loss + 0.2,
                "learning_rate": 0.01 * (0.99 ** i)
            }
            
            exp.log_metrics(metrics, step=i)
            
            # Log an artifact occasionally
            if i % 20 == 0:
                with open(exp.run_dir / f"log_{i}.txt", "w") as f:
                    f.write(f"Log at step {i}\nLoss: {loss}")
            
            if i % 100 == 0:
                exp.info(f"Step {i}: Loss={loss:.4f}, Acc={accuracy:.4f}")

    except KeyboardInterrupt:
        exp.info("Stopped.")

if __name__ == "__main__":
    main()
