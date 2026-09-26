"""
analysis/main.py — legacy entry point (kept for backwards compatibility).

The canonical application entry point is now backend/app/main.py which
runs the universal multi-language scoring pipeline.  This module simply
re-exports the FastAPI app from there so existing test files that import
`from main import app` continue to work.
"""

import sys
from pathlib import Path

# Make the parent app/ directory importable
sys.path.insert(0, str(Path(__file__).parent.parent))

from main import app  # noqa: F401, E402 — re-export
