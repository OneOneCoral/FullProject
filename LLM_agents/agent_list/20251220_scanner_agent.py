from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Dict

from dotenv import load_dotenv
from openai import OpenAI

from Agent.core.base import AgentReport, new_run_id, write_report, REPO_ROOT, PROJECT_ROOTS


ENV_PATH = REPO_ROOT / "Agent" / ".env"
load_dotenv(ENV_PATH)

client = OpenAI()

import inspect
print(inspect.signature(client.responses.create))
print(">>> Agent module loaded:", __name__)


SYSTEM = """You are a scanner for a Python repository.

Return strict JSON with:
{
  "entrypoints": ["<abs path>", ...],
  "notes": ["...", ...],
  "recommended_edit_targets": ["<abs path>", ...]
}

Please read the files in the repository and return a summary of files.
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

    files = {}
    for root in PROJECT_ROOTS:
        files.update(load_python_files(root))
    paths = sorted(files.keys())

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
            text={"format": {"type": "json_object"}},
        )
        raw = resp.output_text
        data = json.loads(raw)

        report = AgentReport(
            agent_name="scanner",
            run_id=run_id,
            created_at=time.time(),
            ok=True,
            summary="Scanned repo for python files.",
            data=data,
            artifacts=[],
        )

    except Exception as e:
        report = AgentReport(
            agent_name="scanner",
            run_id=run_id,
            created_at=time.time(),
            ok=False,
            summary=f"Scanner failed: {e}",
            data={},
            artifacts=[],
        )
    print(json.dumps(report.data, indent=2))
    return write_report(report)

if __name__ == "__main__":
    out = run()

    print("Wrote report:", out)
