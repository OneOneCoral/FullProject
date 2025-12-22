from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import List, Tuple

import sys, os
print("cwd:", os.getcwd())
print("sys.path[0]:", sys.path[0])
print("sys.path:", sys.path)

from base import STATE_DIR, safe_write_text, Change, apply_changes

print(">>> Agent module loaded:", __name__)
# -------------------------
# Minimal framework
# -------------------------
class CreateFileAgent:
    name = "create_file_test"

    def run(self) -> List[Change]:
        # what dose STATE_DIR do?
        target = STATE_DIR / "uploade23.txt"
        content = "up3 from agent!\n\n=^.^=\n"
        return [Change(path=target, summary="Create test file in Agent/state", content=content)]


def main() -> None:
    agent = CreateFileAgent()
    changes = agent.run()
    apply_changes(changes)

if __name__ == "__main__":
    main()