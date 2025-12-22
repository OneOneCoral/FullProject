from __future__ import annotations
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any, Dict, List, Optional
import json
import subprocess
import sys
import time

import os

# -----------------------------
# Paths (single source of truth)
# -----------------------------
REPO_ROOT = Path(__file__).resolve().parent  # .../LLM_agents

STATE_DIR = REPO_ROOT / "state"
REPORTS_DIR = STATE_DIR / "reports"

STATE_DIR.mkdir(parents=True, exist_ok=True)
REPORTS_DIR.mkdir(parents=True, exist_ok=True)

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



# -----------------------------
# Report helpers
# -----------------------------

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

def safe_write_text(path: Path, content: str, *, allow_root: Path = STATE_DIR) -> None:
    path = Path(path)

    # permission guardrail
    try:
        path.resolve().relative_to(allow_root.resolve())
    except ValueError:
        print(f"[SKIP] Not allowed to write outside {allow_root}: {path}")
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


