from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import List, Tuple

import sys, os
print("cwd:", os.getcwd())
print("sys.path[0]:", sys.path[0])
print("sys.path:", sys.path)

#why do i inmport REPO_ROOT (where should this be?/should it not come from somewhere else)
#(dose he know where base is?)
from base import STATE_DIR, safe_write_text, REPO_ROOT

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
        # what dose STATE_DIR do?
        target = STATE_DIR / "uploade2.txt"
        content = "up2 from agent!\n\n=^.^=\n"
        return [Change(path=target, summary="Create test file in Agent/state", content=content)]

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
        safe_write_text(c.path, c.content)  # allow_root defaults to STATE_DIR

def main() -> None:
    agent = CreateFileAgent()
    changes = agent.run()
    apply_changes(changes)

if __name__ == "__main__":
    main()