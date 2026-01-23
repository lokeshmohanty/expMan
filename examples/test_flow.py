import sys
from pathlib import Path
import random
import matplotlib.pyplot as plt
import torch

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from expman import Experiment, ExperimentAnalyzer

def run_experiment():
    print("Starting experiment...")
    # Initialize
    exp = Experiment(experiment_name="test_experiment", run_name="run_001")
    
    # Log config
    exp.log_params({"lr": 0.01, "batch_size": 32, "model": "resnet18"})
    
    # Training Loop Simulation
    for step in range(10):
        loss = 1.0 / (step + 1) + random.random() * 0.1
        accuracy = 0.5 + step * 0.05
        
        # Log metrics
        exp.log_metrics({"loss": loss, "accuracy": accuracy}, step=step)
        
        # Log info
        exp.info(f"Step {step}: loss={loss:.4f}")
        
    # Save Model (async, with graph generation)
    model = torch.nn.Linear(10, 1)
    exp.save_model(model, "final_model.pt", input_size=(1, 10))
    
    # Save Plot
    fig, ax = plt.subplots()
    ax.plot([1, 2, 3], [1, 2, 3], label="Linear")
    ax.set_title("Test Plot")
    ax.legend()
    exp.save_plot(fig, "test_plot.png")
    
    print("Experiment finished.")

def check_analysis():
    print("Verifying analysis...")
    analyzer = ExperimentAnalyzer()
    
    # Check experiments list
    exps = analyzer.get_experiments()
    print(f"Experiments: {exps}")
    assert "test_experiment" in exps
    
    # Check runs
    runs = analyzer.get_runs("test_experiment")
    print(f"Runs: {runs}")
    assert "run_001" in runs
    
    # Check metrics
    df = analyzer.get_run_metrics("test_experiment", "run_001")
    print("Metrics head:")
    print(df.head())
    assert not df.is_empty()
    assert "loss" in df.columns
    
    # Check config
    config = analyzer.get_run_config("test_experiment", "run_001")
    print(f"Config: {config}")
    assert config["lr"] == 0.01

if __name__ == "__main__":
    run_experiment()
    check_analysis()
    print("VERIFICATION SUCCESSFUL")
