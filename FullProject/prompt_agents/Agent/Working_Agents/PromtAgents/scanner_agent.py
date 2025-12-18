from __future__ import annotations

import json
from pathlib import Path
from typing import Dict

from dotenv import load_dotenv
from openai import OpenAI

from pygame.Agent.Working_Agents.base import AgentReport, new_run_id, write_report, REPO_ROOT

ENV_PATH = REPO_ROOT / "Agent" / ".env"
load_dotenv(ENV_PATH)

client = OpenAI()

SYSTEM = """You are a scanner for a Python Pygame repository.

Return strict JSON with:
{
  "entrypoints": ["<abs path>", ...],
  "notes": ["...", ...],
  "recommended_edit_targets": ["<abs path>", ...]
}

Pick entrypoints that likely start a pygame window and contain a main loop.
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
    run_id = new_run_id("scanner")
    files = load_python_files(REPO_ROOT)
    paths = sorted(files.keys())

    # Provide a small sample of likely candidates
    likely = [p for p in paths if p.endswith(("main.py", "game.py", "app.py", "run.py"))]
    payload = {
        "repo_root": str(REPO_ROOT),
        "python_files_count": len(paths),
        "python_files": paths[:400],
        "likely_candidates": {p: files[p][:4000] for p in likely[:10]},
    }

    try:
        resp = client.responses.create(
            model="gpt-4.1",
            input=[
                {"role": "system", "content": SYSTEM},
                {"role": "user", "content": json.dumps(payload)},
            ],
        )
        data = json.loads(resp.output_text)
        report = AgentReport(
            agent_name="scanner",
            run_id=run_id,
            created_at=__import__("time").time(),
            ok=True,
            summary="Scanned repo for likely entrypoints and main loops.",
            data=data,
            artifacts=[],
        )
    except Exception as e:
        report = AgentReport(
            agent_name="scanner",
            run_id=run_id,
            created_at=__import__("time").time(),
            ok=False,
            summary=f"Scanner failed: {e}",
            data={},
            artifacts=[],
        )

    return write_report(report)

if __name__ == "__main__":
    out = run()
    print("Wrote report:", out)
