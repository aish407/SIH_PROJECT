"""Reliable local launcher for RoadWatch when a virtualenv launcher is unavailable."""

import os
import runpy
from pathlib import Path

import uvicorn


ROOT = Path(__file__).resolve().parents[1]
application = runpy.run_path(str(ROOT / "app" / "main.py"))["app"]

if __name__ == "__main__":
    uvicorn.run(application, host="127.0.0.1", port=int(os.environ.get("PORT", "8004")))
