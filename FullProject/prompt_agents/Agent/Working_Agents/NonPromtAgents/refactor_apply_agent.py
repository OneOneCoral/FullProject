from __future__ import annotations

import os
import shutil
from pathlib import Path
from time import time

from pygame.Agent.Working_Agents.base import AgentReport, new_run_id, write_report, read_latest_report, REPO_ROOT

DRY_RUN = os.getenv("CODERUNNERX_DRY_RUN", "true").lower() in ("1", "true", "yes")
APPLY = os.getenv("CODERUNNERX_APPLY_REFACTOR", "false").lower() in ("1", "true", "yes")

BACKUP_DIR = REPO_ROOT / "Agent" / ".coderunnerx" / "backups"
BACKUP_DIR.mkdir(parents=True, exist_ok=True)

def ensure_parent(path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)

def backup_file(src: Path, run_id: str) -> Path:
    dst = BACKUP_DIR / f"{src.name}.backup.{run_id}"
    shutil.copy2(src, dst)
    return dst

def run() -> Path:
    run_id = new_run_id("refactor_apply")
    plan = read_latest_report("organize_plan")
    if not plan or not plan.get("ok", False):
        return write_report(AgentReport(
            agent_name="refactor_apply",
            run_id=run_id,
            created_at=time(),
            ok=False,
            summary="No valid organize_plan report found. Run organize_plan first.",
            data={},
            artifacts=[],
        ))

    data = plan.get("data", {})
    moves = data.get("moves", [])
    batches = data.get("batches", [])

    # Apply only the first batch by default (safe)
    batch = batches[0] if batches else {"name": "batch_1", "moves": list(range(min(3, len(moves))))}
    move_idxs = batch.get("moves", [])
    applied = []
    artifacts = []

    if DRY_RUN or not APPLY:
        return write_report(AgentReport(
            agent_name="refactor_apply",
            run_id=run_id,
            created_at=time(),
            ok=True,
            summary="Dry-run: refactor plan NOT applied (set CODERUNNERX_APPLY_REFACTOR=true and CODERUNNERX_DRY_RUN=false).",
            data={"selected_batch": batch, "would_move": [moves[i] for i in move_idxs if 0 <= i < len(moves)]},
            artifacts=[],
        ))

    for i in move_idxs:
        if i < 0 or i >= len(moves):
            continue
        m = moves[i]
        src = Path(m["from"])
        dst = Path(m["to"])

        if not src.exists():
            continue

        ensure_parent(dst)
        # backup before move
        artifacts.append(str(backup_file(src, run_id)))

        # move
        shutil.move(str(src), str(dst))
        applied.append({"from": str(src), "to": str(dst), "reason": m.get("reason", "")})
        artifacts.append(str(dst))

        # ensure packages have __init__.py
        # if moved into .../game/entities/player.py ensure game/__init__.py exists etc.
        for parent in [dst.parent, *dst.parents]:
            if parent == REPO_ROOT:
                break
            # create __init__.py for python packages inside repo
            init = parent / "__init__.py"
            # only create if parent contains python files/folders likely used as package
            if parent.name in ("game", "entities", "systems", "ui") or (parent / "__init__.py").exists():
                init.touch(exist_ok=True)

    return write_report(AgentReport(
        agent_name="refactor_apply",
        run_id=run_id,
        created_at=time(),
        ok=True,
        summary=f"Applied {len(applied)} file moves from {batch.get('name','batch')}.",
        data={"selected_batch": batch, "applied_moves": applied},
        artifacts=artifacts,
    ))

if __name__ == "__main__":
    out = run()
    print("Wrote report:", out)
