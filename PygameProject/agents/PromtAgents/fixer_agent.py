from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Dict, List

from dotenv import load_dotenv
from openai import OpenAI

from pygame.Agent.Working_Agents.base import AgentReport, new_run_id, write_report, read_latest_report, REPO_ROOT

ENV_PATH = REPO_ROOT / "Agent" / ".env"
load_dotenv(ENV_PATH)

client = OpenAI()

DRY_RUN = os.getenv("CODERUNNERX_DRY_RUN", "true").lower() in ("1", "true", "yes")

# You control blast radius here:
ALLOWED_PATHS: List[str] = []  # if empty, will use scanner recommended_edit_targets (capped)

SYSTEM = """You are a fixer for a Python Pygame repository.

Primary goal:
- Ensure a working entrypoint main loop (init, display, QUIT, clock.tick, quit).
- Minimal edits, reuse existing classes if imports are clean.

Output strict JSON:
{ "path": "<abs path>", "summary": "<1-2 sentences>", "updated_code": "<full file text>" }
Return ONLY JSON.
"""

def load_python_files(repo_root: Path) -> Dict[str, str]:
    files: Dict[str, str] = {}
    for p in repo_root.rglob("*.py"):
        s = str(p)
        if any(x in s for x in ["/.git/", "\\.git\\", "/venv/", "\\venv\\", "__pycache__"]):
            continue
        try:
            files[s] = p.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
    return files

def run() -> Path:
    run_id = new_run_id("fixer")
    files = load_python_files(REPO_ROOT)

    scan = read_latest_report("scanner")
    recommended = (scan or {}).get("recommended_edit_targets", [])
    targets = ALLOWED_PATHS[:] if ALLOWED_PATHS else recommended[:5]  # cap

    changes = []
    artifacts = []

    for path in targets:
        if path not in files:
            continue
        payload = {
            "path": path,
            "code": files[path],
            "repo_root": str(REPO_ROOT),
            "scanner_notes": (scan or {}).get("notes", []),
        }
        resp = client.responses.create(
            model="gpt-4.1",
            input=[
                {"role": "system", "content": SYSTEM},
                {"role": "user", "content": json.dumps(payload)},
            ],
        )
        data = json.loads(resp.output_text)
        updated = data["updated_code"]
        if updated != files[path]:
            changes.append({"path": path, "summary": data.get("summary", "")})
            artifacts.append(path)
            if not DRY_RUN:
                Path(path).write_text(updated, encoding="utf-8")

    report = AgentReport(
        agent_name="fixer",
        run_id=run_id,
        created_at=__import__("time").time(),
        ok=True,
        summary=("Proposed fixes (dry-run)." if DRY_RUN else "Applied fixes."),
        data={"dry_run": DRY_RUN, "changes": changes, "targets": targets},
        artifacts=artifacts,
    )
    return write_report(report)

if __name__ == "__main__":
    out = run()
    print("Wrote report:", out)
