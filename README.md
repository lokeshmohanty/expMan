# ExpMan: Experiment Manager

![GitHub Release](https://img.shields.io/github/v/release/lokeshmohanty/expMan)

`expman` is a lightweight, functional research experiment management library.

## Features

- **Functional Core**: Pure functions for reliable data management
- **Universal Tracking**: Metrics (Parquet), Config (YAML), Models (PyTorch), Plots (PD/Matplotlib)
- **Modern Web Dashboard**: 
  - **Run Comparison**: Overlay metrics from multiple runs on interactive Plotly charts.
  - **Artifact Browser**: Browse and preview all experiment files including auto-generated model architecture graphs.

  ![Dashboard Metrics](assets/dashboard_metrics.png)
  ![Dashboard Artifacts](assets/dashboard_artifacts.png)

## Installation

- **Basic Installation** (Lightweight, no Torch/Graphviz):
```bash
pip install git+https://github.com/lokeshmohanty/expMan.git
```

- **Full Installation** (With PyTorch support for model saving & architecture graphs) 
   (you can also choose to install torch, torchview and graphviz separately using the basic installation):
```bash
pip install "expman[torch] @ git+https://github.com/lokeshmohanty/expMan.git"
```

## Development

To develop `expman` (with frontend watch and backend reload):
```bash
expman dev
```


## Quick Start

1. **Run an Experiment**:
   ```python
   from expman import Experiment
   import matplotlib.pyplot as plt
   import torch
   import torchvision

   # Initialize
   exp = Experiment("my_experiment")
   exp.log_params({"lr": 0.001, "model": "resnet18"})

   # Training Loop
   for i in range(100):
       exp.log_metrics({"loss": 0.5 - i*0.001, "accuracy": i*0.01}, step=i)
   
   # Save Artifacts & Auto-Generate Model Graph
   # Saving is non-blocking (runs in background thread)
   model = torchvision.models.resnet18()
   exp.save_model(model, "final.pt", input_size=(1, 3, 224, 224)) 
   ```

   For a complete example, check [examples/test_run.py](examples/test_run.py).

2. **Launch Dashboard**:
   ```bash
   expman serve ./experiments
   ```
   Open [http://localhost:8000](http://localhost:8000)

3. **Interactive Analysis**:
   Load a run directly into a Python REPL with metrics and config pre-loaded:
   ```bash
   expman load experiments/my_experiment/runs/run_001
   ```

   ![Interactive Analysis Preview](assets/interactive_analysis_preview.png)
