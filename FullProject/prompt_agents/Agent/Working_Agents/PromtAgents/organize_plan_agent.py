from __future__ import annotations

import json
from time import time
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI

from pygame.Agent.Working_Agents.base import AgentReport, new_run_id, write_report, read_latest_report, REPO_ROOT

ENV_PATH = REPO_ROOT / "Agent" / ".env"
load_dotenv(ENV_PATH)
client = OpenAI()

SYSTEM = """You are an organizer/planner for a Python Pygame repository.

Input: an inventory index of pygame-relevant files with their functions/classes.

Task:
- Propose a clean module/package structure for the game code.
- Produce a refactor plan that is SAFE and incremental:
  - define target package layout (folders/files)
  - propose file moves (old_path -> new_path)
  - propose import updates needed
  - propose "batch" steps (small groups of moves) so we can test each batch
- Keep behavior the same; do NOT redesign the game.
- Prefer grouping by responsibility:
  - game/loop.py (main loop)
  - game/entities/ (Player, Enemy, ...)
  - game/systems/ (collision, physics, input)
  - game/ui/
  - game/assets/ (if relevant, though assets aren't python)
- If code lives in dated test folders, propose leaving them as examples unless user intends otherwise.

Output strict JSON ONLY:
{
  "target_layout": ["game/__init__.py", "game/loop.py", ...],
  "moves": [{"from": "<abs>", "to": "<abs>", "reason": "..."}],
  "import_updates_notes": ["..."],
  "batches": [
    {"name": "batch_1", "moves": [0,1,2], "notes": "..."},
    ...
  ]
}
"""

def run() -> Path:
    run_id = new_run_id("organize_plan")
    inv = read_latest_report("inventory")
    if not inv or not inv.get("ok", False):
        report = AgentReport(
            agent_name="organize_plan",
            run_id=run_id,
            created_at=time(),
            ok=False,
            summary="No valid inventory report found. Run inventory first.",
            data={},
            artifacts=[],
        )
        return write_report(report)

    payload = {
        "repo_root": str(REPO_ROOT),
        "inventory_summary": inv.get("summary", ""),
        "index": inv.get("data", {}).get("index", [])[:200],  # cap
    }

    resp = client.responses.create(
        model="gpt-4.1",
        input=[
            {"role": "system", "content": SYSTEM},
            {"role": "user", "content": json.dumps(payload)},
        ],
    )
    data = json.loads(resp.output_text)

    report = AgentReport(
        agent_name="organize_plan",
        run_id=run_id,
        created_at=time(),
        ok=True,
        summary="Produced an incremental refactor plan to organize game code.",
        data=data,
        artifacts=[],
    )
    return write_report(report)

if __name__ == "__main__":
    out = run()
    print("Wrote report:", out)
