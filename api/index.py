"""Vercel Serverless Function entry point for LedgerLine FastAPI."""

import sys
from pathlib import Path

# Add backend directory to sys.path
_root = Path(__file__).resolve().parent.parent
_backend = _root / "backend"

if str(_backend) not in sys.path:
    sys.path.insert(0, str(_backend))
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))

from app.main import app  # noqa: E402
