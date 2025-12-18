from __future__ import annotations

import os
import shutil
from pathlib import Path
from time import time

from pygame.Agent.Working_Agents.base import AgentReport, new_run_id, write_report, REPO_ROOT

# Default: promote the latest dated entrypoint you already have
DEFAULT_SOURCE = str(REPO_ROOT / "PygameTest" / "20251024" / "main.py")
TARGET = str(REPO_ROOT / "main.py")

# Optional override via env var:
# CODERUNNERX_PROMOTE_SOURCE=C:\...\PygameTest\20251020\Classes\main.py
SOURCE = os.getenv("CODERUNNERX_PROMOTE_SOURCE", DEFAULT_SOURCE)

# Safety: make a backup of current root main.py (if it exists)
BACKUP_DIR = REPO_ROOT / "Agent" / ".coderunnerx" / "backups"
BACKUP_DIR.mkdir(parents=True, exist_ok=True)

def run() -> Path:
    run_id = new_run_id("promote_entrypoint")
    artifacts = []

    src = Path(SOURCE)
    dst = Path(TARGET)

    if not src.exists():
        report = AgentReport(
            agent_name="promote_entrypoint",
            run_id=run_id,
            created_at=time(),
            ok=False,
            summary=f"Source entrypoint not found: {src}",
            data={"source": str(src), "target": str(dst)},
            artifacts=[],
        )
        return write_report(report)

    # backup existing target
    if dst.exists():
        backup_path = BACKUP_DIR / f"main.py.backup.{run_id}"
        shutil.copy2(dst, backup_path)
        artifacts.append(str(backup_path))

    # copy source -> target
    shutil.copy2(src, dst)
    artifacts.extend([str(src), str(dst)])

    report = AgentReport(
        agent_name="promote_entrypoint",
        run_id=run_id,
        created_at=time(),
        ok=True,
        summary="Promoted dated entrypoint to repo-root main.py (backup created if needed).",
        data={"source": str(src), "target": str(dst)},
        artifacts=artifacts,
    )
    return write_report(report)

if __name__ == "__main__":
    out = run()
    print("Wrote report:", out)
    print("Promoted:", SOURCE, "->", TARGET)
