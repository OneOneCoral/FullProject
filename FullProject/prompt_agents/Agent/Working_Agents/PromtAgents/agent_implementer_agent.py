from __future__ import annotations

import json
import os
import difflib
from time import time
from pathlib import Path
from typing import Dict, List

from dotenv import load_dotenv
from openai import OpenAI

from pygame.Agent.Working_Agents.base import AgentReport, new_run_id, write_report, REPO_ROOT, read_latest_report

ENV_PATH = REPO_ROOT / "Agent" / ".env"
load_dotenv(ENV_PATH)
client = OpenAI()

DRY_RUN = os.getenv("CODERUNNERX_DRY_RUN", "true").lower() in ("1", "true", "yes")
APPLY = os.getenv("CODERUNNERX_APPLY_AGENT_IMPROVEMENTS", "false").lower() in ("1", "true", "yes")

SYSTEM = """You are an implementer agent that edits agent tooling code safely.

You are given:
- selected improvement suggestions
- current contents of target files

Task:
- Apply minimal safe changes that implement the suggestions.
- Keep behavior conservative.
- Do not break imports.

Return strict JSON ONLY:
{
  "changes": [
    {"path": "<abs path>", "summary": "...", "updated_code": "<full file text>"}
  ]
}
"""

def print_suggestions(suggestions: List[dict]) -> None:
    print("\nAvailable improvement suggestions:\n")
    for s in suggestions:
        print(f"  {s['id']:>2}) {s.get('title','(no title)')}")
        print(f"      Reason: {s.get('reason','')}")
        tfs = s.get("target_files", [])
        if tfs:
            print(f"      Files: {', '.join(Path(x).name for x in tfs)}")
        print()

def parse_selection(inp: str, valid_ids: set[int]) -> List[int]:
    inp = inp.strip().lower()
    if inp in ("q", "quit", "exit"):
        raise SystemExit(0)
    if inp in ("all",):
        return sorted(valid_ids)

    parts = [p.strip() for p in inp.split(",") if p.strip()]
    chosen = []
    for p in parts:
        if p.isdigit():
            i = int(p)
            if i in valid_ids:
                chosen.append(i)
    return sorted(set(chosen))

def unified_diff(path: str, before: str, after: str) -> str:
    a = before.splitlines(keepends=True)
    b = after.splitlines(keepends=True)
    diff = difflib.unified_diff(a, b, fromfile=path + " (before)", tofile=path + " (after)")
    return "".join(diff)

def run() -> Path:
    run_id = new_run_id("agent_implementer")

    review = read_latest_report("agent_review")
    if not review or not review.get("ok", False):
        return write_report(AgentReport(
            agent_name="agent_implementer",
            run_id=run_id,
            created_at=time(),
            ok=False,
            summary="No agent_review report found. Run agent_review first.",
            data={},
            artifacts=[],
        ))

    suggestions = review.get("data", {}).get("suggestions", [])
    if not suggestions:
        return write_report(AgentReport(
            agent_name="agent_implementer",
            run_id=run_id,
            created_at=time(),
            ok=True,
            summary="No suggestions to implement.",
            data={},
            artifacts=[],
        ))

    # interactive selection
    print_suggestions(suggestions)
    valid_ids = {int(s["id"]) for s in suggestions if "id" in s}
    choice = input("Select suggestions by number (e.g. 1,3) | 'all' | 'q': ")
    selected_ids = parse_selection(choice, valid_ids)

    selected = [s for s in suggestions if int(s["id"]) in selected_ids]
    if not selected:
        return write_report(AgentReport(
            agent_name="agent_implementer",
            run_id=run_id,
            created_at=time(),
            ok=False,
            summary="No valid suggestions selected.",
            data={"selected_ids": selected_ids},
            artifacts=[],
        ))

    # Load current target files
    targets = sorted({p for s in selected for p in s.get("target_files", [])})
    file_map: Dict[str, str] = {}
    for p in targets:
        pp = Path(p)
        if pp.exists():
            file_map[str(pp)] = pp.read_text(encoding="utf-8", errors="ignore")

    payload = {
        "repo_root": str(REPO_ROOT),
        "selected_suggestions": selected,
        "files": file_map,
    }

    resp = client.responses.create(
        model="gpt-4.1",
        input=[
            {"role": "system", "content": SYSTEM},
            {"role": "user", "content": json.dumps(payload)},
        ],
    )
    data = json.loads(resp.output_text)
    changes = data.get("changes", [])

    # Preview diffs
    diffs = []
    for c in changes:
        path = c["path"]
        after = c["updated_code"]
        before = file_map.get(path, "")
        diffs.append({"path": path, "diff": unified_diff(path, before, after), "summary": c.get("summary", "")})

    print("\n=== DIFF PREVIEW ===\n")
    for d in diffs:
        print(f"# {d['path']}")
        print(f"# {d['summary']}\n")
        print(d["diff"] if d["diff"].strip() else "(no diff)")
        print("\n" + "-"*80 + "\n")

    # Apply gate
    if DRY_RUN or not APPLY:
        print("Not applying changes (set CODERUNNERX_DRY_RUN=false and CODERUNNERX_APPLY_AGENT_IMPROVEMENTS=true).")
        report = AgentReport(
            agent_name="agent_implementer",
            run_id=run_id,
            created_at=time(),
            ok=True,
            summary="Dry-run: generated diffs for selected suggestions.",
            data={"selected_ids": selected_ids, "diffs": diffs, "dry_run": DRY_RUN, "apply_enabled": APPLY},
            artifacts=[c["path"] for c in changes],
        )
        return write_report(report)

    confirm = input("Apply these changes? (y/N): ").strip().lower()
    if confirm != "y":
        report = AgentReport(
            agent_name="agent_implementer",
            run_id=run_id,
            created_at=time(),
            ok=True,
            summary="User declined to apply changes.",
            data={"selected_ids": selected_ids, "diffs": diffs},
            artifacts=[],
        )
        return write_report(report)

    # Apply
    for c in changes:
        Path(c["path"]).write_text(c["updated_code"], encoding="utf-8")

    report = AgentReport(
        agent_name="agent_implementer",
        run_id=run_id,
        created_at=time(),
        ok=True,
        summary="Applied selected agent improvements.",
        data={"selected_ids": selected_ids, "applied": [c["path"] for c in changes]},
        artifacts=[c["path"] for c in changes],
    )
    return write_report(report)

if __name__ == "__main__":
    out = run()
    print("Wrote report:", out)
