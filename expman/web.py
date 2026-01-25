from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
import uvicorn
from pathlib import Path
import math

from expman.analysis import ExperimentAnalyzer

app = FastAPI()
import os
analyzer = ExperimentAnalyzer(base_dir=os.environ.get("EXPMAN_BASE_DIR", "experiments"))

# Mount static files
static_dir = Path(__file__).parent / "static"
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

@app.get("/")
async def index():
    if not static_dir.exists():
        return HTMLResponse("<h1>ExpMan Server Running</h1><p>Frontend assets not found. Use 'expman dev' or build the frontend.</p>")
    return HTMLResponse(content=(static_dir / "index.html").read_text())

@app.get("/api/experiments")
async def list_experiments():
    return analyzer.get_experiments()

@app.get("/api/experiments/{experiment_name}/runs")
async def list_runs(experiment_name: str):
    return analyzer.get_runs(experiment_name)

@app.get("/api/experiments/{experiment_name}/stats")
async def get_experiment_stats(experiment_name: str):
    return analyzer.get_experiment_stats(experiment_name)

@app.get("/api/experiments/{experiment_name}/metadata")
async def get_experiment_metadata(experiment_name: str):
    # Retrieve metadata directly using utils (via analyzer base_dir context)
    # Or add method to analyzer. Let's do it here for simplicity or via analyzer.
    # Analyzer knows the path.
    exp_dir = analyzer.base_dir / experiment_name
    from expman import io as utils
    return utils.load_experiment_metadata(exp_dir)

from pydantic import BaseModel
class MetadataUpdate(BaseModel):
    description: str = ""
    display_name: str = ""

@app.post("/api/experiments/{experiment_name}/metadata")
async def update_experiment_metadata(experiment_name: str, meta: MetadataUpdate):
    exp_dir = analyzer.base_dir / experiment_name
    from expman import io as utils
    
    current = utils.load_experiment_metadata(exp_dir)
    current.update(meta.dict())
    utils.save_experiment_metadata(exp_dir, current)

    return current

@app.get("/api/experiments/{experiment_name}/runs/{run_name}/metadata")
async def get_run_metadata(experiment_name: str, run_name: str):
    run_dir = analyzer.base_dir / experiment_name / "runs" / run_name
    from expman import io as utils
    return utils.load_run_metadata(run_dir)

@app.post("/api/experiments/{experiment_name}/runs/{run_name}/metadata")
async def update_run_metadata(experiment_name: str, run_name: str, meta: MetadataUpdate):
    run_dir = analyzer.base_dir / experiment_name / "runs" / run_name
    from expman import io as utils
    
    current = utils.load_run_metadata(run_dir)
    current.update(meta.dict())
    utils.save_run_metadata(run_dir, current)
    return current


@app.get("/api/experiments/{experiment_name}/runs/{run_name}/metrics")
async def get_metrics(experiment_name: str, run_name: str, since_step: int = None):
    df = analyzer.get_run_metrics(experiment_name, run_name, since_step=since_step)
    if df.is_empty():
        return []
    
    data = df.to_dicts()
    sanitized = []
    for row in data:
        new_row = {}
        for k, v in row.items():
            if isinstance(v, float) and (math.isnan(v) or math.isinf(v)):
                new_row[k] = None
            else:
                new_row[k] = v
        sanitized.append(new_row)
    return sanitized

@app.get("/api/experiments/{experiment_name}/runs/{run_name}/config")
async def get_config(experiment_name: str, run_name: str):
    return analyzer.get_run_config(experiment_name, run_name)
@app.get("/api/config")
async def get_server_config():
    return {
        "live_mode": analyzer.live_mode
    }




# --- Artifact Browser ---

@app.get("/api/experiments/{experiment_name}/runs/{run_name}/artifacts_list")
async def list_artifacts(experiment_name: str, run_name: str):
    """Lists files in the run directory."""
    run_dir = analyzer.base_dir / experiment_name / "runs" / run_name
    if not run_dir.exists():
        return []
    
    files = []
    # Use rglob for deep listing or glob for shallow. Let's do recursive.
    for p in run_dir.rglob("*"):
        if p.is_file():
            rel_path = p.relative_to(run_dir)
            files.append({
                "path": str(rel_path),
                "name": p.name,
                "size": p.stat().st_size,
                "type": p.suffix.lower()
            })
    return files

@app.get("/api/experiments/{experiment_name}/runs/{run_name}/artifacts/content")
async def get_artifact_content(experiment_name: str, run_name: str, path: str):
    """Serves the content of an artifact file."""
    run_dir = analyzer.base_dir / experiment_name / "runs" / run_name
    file_path = (run_dir / path).resolve()
    
    # Security check: ensure we don't escape run_dir
    if not str(file_path).startswith(str(run_dir.resolve())):
        return JSONResponse({"error": "Access denied"}, status_code=403)
        
    if not file_path.exists():
        return JSONResponse({"error": "File not found"}, status_code=404)

    # For Parquet/CSV, we might want to return JSON data instead of raw file?
    # Requirement: "data like parquet, csv, ... should be viewable"
    if file_path.suffix == ".parquet":
        import polars as pl
        try:
            df = pl.read_parquet(file_path)
            # Preview first 100 rows
            return JSONResponse({"type": "parquet", "data": df.head(100).to_dicts(), "columns": df.columns})
        except Exception as e:
            return JSONResponse({"error": f"Failed to read parquet: {e}"}, status_code=500)
            
    if file_path.suffix == ".csv":
        import polars as pl
        try:
            df = pl.read_csv(file_path)
            return JSONResponse({"type": "csv", "data": df.head(100).to_dicts(), "columns": df.columns})
        except Exception as e:
             return JSONResponse({"error": f"Failed to read csv: {e}"}, status_code=500)

    # For media and others, serve raw file
    media_type = None
    if file_path.suffix in ['.png', '.jpg', '.jpeg']: media_type = "image/jpeg"
    elif file_path.suffix in ['.mp4']: media_type = "video/mp4"
    elif file_path.suffix in ['.json']: media_type = "application/json"
    elif file_path.suffix in ['.yaml', '.yml']: media_type = "text/yaml"
    elif file_path.suffix in ['.txt', '.log']: media_type = "text/plain"
    elif file_path.suffix in ['.svg']: media_type = "image/svg+xml"
    
    return FileResponse(file_path, media_type=media_type)


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--experiments-dir", default="./experiments")
    parser.add_argument("--no-live", action="store_true", help="Disable live mode (auto-refresh)")
    args = parser.parse_args()
    
    global analyzer
    analyzer = ExperimentAnalyzer(base_dir=args.experiments_dir)
    analyzer.live_mode = not args.no_live
    
    print(f"Starting ExpMan UI at http://{args.host}:{args.port}")
    if analyzer.live_mode:
        print("Live mode ENABLED")
    else:
        print("Live mode DISABLED")
    
    uvicorn.run(app, host=args.host, port=args.port)

if __name__ == "__main__":
    main()
