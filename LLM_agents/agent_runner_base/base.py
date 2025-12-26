from __future__ import annotations
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any, Dict, List, Optional
import json
import os
import subprocess
import sys
import time

from .base_utility.write_json import write_json_atomic, emit_message
from .base_utility.publish_text import publish_text

# -----------------------------
# Paths (single source of truth)
# -----------------------------
REPO_ROOT = Path(__file__).resolve().parent  # .../LLM_agents

STATE_DIR = REPO_ROOT / "state"
STATE_DIR.mkdir(parents=True, exist_ok=True)

REPORTS_DIR = STATE_DIR / "reports"
REPORTS_DIR.mkdir(parents=True, exist_ok=True)

GAME_DIR = REPO_ROOT / "game"
GAME_DIR.mkdir(parents=True, exist_ok=True)

ALLOWED_WRITE_ROOTS = [STATE_DIR, GAME_DIR]

# LLM-visible project roots (optional)
PROJECT_ROOTS = [REPO_ROOT]

# -----------------------------
# Report model (agent contract)
# -----------------------------
@dataclass
class AgentReport:
    agent_name: str
    run_id: str
    created_at: float
    ok: bool
    summary: str
    data: Dict[str, Any]
    artifacts: List[str]


@dataclass
class Change:
    path: Path
    summary: str
    content: str

def is_dry_run() -> bool:
    return os.getenv("CODERUNNERX_DRY_RUN", "false").lower() == "true"

def new_run_id(agent_name: str) -> str:
    ts = time.strftime("%Y%m%d-%H%M%S")
    return f"{agent_name}-{ts}"


def write_report(report: AgentReport) -> Path:
    path = REPORTS_DIR / f"{report.run_id}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(asdict(report), indent=2), encoding="utf-8")
    return path

def read_latest_report(agent_name: str) -> Optional[Dict[str, Any]]:
    files = sorted(REPORTS_DIR.glob(f"{agent_name}-*.json"))
    if not files:
        return None
    return json.loads(files[-1].read_text(encoding="utf-8"))

def safe_write_text(path: Path, content: str, *, allow_roots: list[Path] | None = None) -> None:
    path = Path(path)
    allow_roots = allow_roots or [STATE_DIR]

    resolved = path.resolve()
    ok = False
    for root in allow_roots:
        try:
            resolved.relative_to(root.resolve())
            ok = True
            break
        except ValueError:
            pass

    if not ok:
        print(f"[SKIP] Not allowed to write outside: {[str(r) for r in allow_roots]} :: {path}")
        return

    path.parent.mkdir(parents=True, exist_ok=True)

    if is_dry_run():
        print(f"[DRY_RUN] Would write: {path}")
        return

    path.write_text(content, encoding="utf-8")
    print(f"[WRITE] File written: {path}")

# -----------------------------
# Run a child agent (module)
# -----------------------------
def run_child(module: str) -> int:
    """
    Runs: python -m <module> from repo root so imports work.
    Example module: "Agent.agents.scanner_agent"
    """
    proc = subprocess.run([sys.executable, "-m", module], cwd=str(REPO_ROOT), check=False)
    return proc.returncode

def apply_changes(changes: List[Change]) -> None:
    if not changes:
        print("No changes.")
        return

    print("Repo root:", REPO_ROOT)
    print("STATE_DIR:", STATE_DIR)
    print("\nPlanned changes:")
    for c in changes:
        print(f"- {c.path} :: {c.summary}")

    for c in changes:
        p = Path(c.path)
        if not p.is_absolute():
            p = (REPO_ROOT / p)
        safe_write_text(p, c.content, allow_roots=ALLOWED_WRITE_ROOTS)
