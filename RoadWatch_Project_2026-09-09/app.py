"""Compatibility entry point for the RoadWatch GIS FastAPI application."""

import importlib.util
from pathlib import Path

_main_path = Path(__file__).parent / "app" / "main.py"
_spec = importlib.util.spec_from_file_location("roadwatch_main", _main_path)
if _spec is None or _spec.loader is None:
    raise RuntimeError("Could not load app/main.py")
_module = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_module)
app = _module.app


if __name__ == "__main__":
    import os
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=int(os.environ.get("PORT", "8000")))
