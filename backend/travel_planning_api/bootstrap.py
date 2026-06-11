"""Shared bootstrap helpers for project-root and backend-package import setup."""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
BACKEND_ROOT = PROJECT_ROOT / "backend"


def ensure_project_paths() -> None:
    """Ensure project root and backend package paths are importable.

    Keep the repository root importable so package imports like
    `travel_planning_agent_runtime...` and `config...` remain stable across entrypoints,
    and keep `backend/` importable so direct `travel_planning_api...` imports resolve in
    tests and local scripts without per-file `sys.path` patches.
    """
    for path in (str(PROJECT_ROOT), str(BACKEND_ROOT)):
        if path not in sys.path:
            sys.path.insert(0, path)
