from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import List, Tuple

import sys, os
print("cwd:", os.getcwd())
print("sys.path[0]:", sys.path[0])
print("sys.path:", sys.path)

from Agent.core.base import REPO_ROOT, STATE_DIR, is_dry_run, safe_write_text

print(">>> Agent module loaded:", __name__)
# -------------------------
# Minimal framework
# -------------------------
@dataclass
class Change:
    path: Path
    summary: str
    content: str


class CreateFileAgent:
    name = "create_file_test"

    def run(self) -> List[Change]:
        target = STATE_DIR / "uploade.txt"
        content = "up from agent!\n\n=^.^=\n"
        return [Change(path=target, summary="Create test file in Agent/state", content=content)]


def is_allowed_to_edit(path: Path) -> bool:
    # hard safety: only allow writes inside Agent/state
    try:
        path.resolve().relative_to(STATE_DIR.resolve())
        return True
    except ValueError:
        return False


def apply_changes(changes: List[Change]) -> None:
    if not changes:
        print("No changes.")
        return

    print("Repo root:", REPO_ROOT)
    print("STATE_DIR:", STATE_DIR)
    print("\nPlanned changes:")
    for c in changes:
        print(f"- {c.path} :: {c.summary}")

    if is_dry_run:
        print("\nDRY_RUN is enabled -> not writing files.")
        print("Set CODERUNNERX_DRY_RUN=false to actually write.")
        return

    for c in changes:
        if not is_allowed_to_edit(c.path):
            print(f"[skip] not allowed: {c.path}")
            continue
        c.path.parent.mkdir(parents=True, exist_ok=True)
        c.path.write_text(c.content, encoding="utf-8")
        print(f"[write] {c.path}")


def main() -> None:
    agent = CreateFileAgent()
    changes = agent.run()
    apply_changes(changes)


if __name__ == "__main__":
    main()