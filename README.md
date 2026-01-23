# ExpMan

`expman` is a lightweight, functional research experiment management library.

## Features

- **Functional Core**: Pure functions for reliable data management
- **Universal Tracking**: Metrics (Parquet), Config (YAML), Models (PyTorch), Plots (PD/Matplotlib)
- **Modern Web Dashboard**: 
  - **Run Comparison**: Overlay metrics from multiple runs on interactive Plotly charts.
  - **Artifact Browser**: Browse and preview all experiment files including auto-generated model architecture graphs.

## Setup

1. **Install with uv**:
   ```bash
   uv init
   uv add expman[viz]
   # Or for local dev:
   uv init
   uv add loguru polars pyyaml torch matplotlib fastapi uvicorn pyarrow torchview
   uv pip install -e .
   ```
   
   > [!IMPORTANT]
   > For model visualization:
   > 1. Install graphviz: `sudo apt-get install graphviz` (Linux) or `brew install graphviz` (Mac)
   > 2. Pass `input_size` to `exp.save_model` to auto-generate the SVG.

2. **Run an Experiment**:
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

   For a complete example, check [examples/test_flow.py](examples/test_flow.py).

3. **Launch Dashboard**:
   ```bash
   uv run python -m expman.server --experiments-dir ./experiments
   ```
   Open [http://localhost:8000](http://localhost:8000)
