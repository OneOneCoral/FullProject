from __future__ import annotations

import subprocess
from pathlib import Path
from typing import List, Tuple

from pygame.Agent.Working_Agents.base import AgentReport, new_run_id, write_report, read_latest_report, REPO_ROOT

def py_compile(paths: List[str]) -> List[Tuple[str, int, str]]:
    results = []
    for p in paths:
        proc = subprocess.run(["python", "-m", "py_compile", p], cwd=str(REPO_ROOT),
                              capture_output=True, text=True, check=False)
        out = (proc.stdout or "") + ("\n" + proc.stderr if proc.stderr else "")
        results.append((p, proc.returncode, out.strip()))
    return results

def run() -> Path:
    run_id = new_run_id("smoke_test")

    fixer = read_latest_report("fixer") or {}
    paths = fixer.get("artifacts") or fixer.get("data", {}).get("changes", [])
    # Handle both formats:
    if paths and isinstance(paths[0], dict):
        paths = [c["path"] for c in paths]

    results = py_compile(paths) if paths else []
    ok = all(rc == 0 for _, rc, _ in results)

    report = AgentReport(
        agent_name="smoke_test",
        run_id=run_id,
        created_at=__import__("time").time(),
        ok=ok,
        summary="py_compile checks passed." if ok else "py_compile found errors.",
        data={"results": [{"path": p, "rc": rc, "output": out} for p, rc, out in results]},
        artifacts=paths,
    )
    return write_report(report)

if __name__ == "__main__":
    out = run()
    print("Wrote report:", out)
