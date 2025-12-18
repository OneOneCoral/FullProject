from __future__ import annotations

from pathlib import Path
import os
import time

from Agent.Working_Agents.base import (
    AgentReport,
    new_run_id,
    write_report,
    read_json,
    REPO_ROOT,
    log,
)

def run() -> Path:
    run_id = new_run_id("implementer")

    selection_path = REPO_ROOT / "Agent" / "selected_agent_improvements.json"
    selection = read_json(selection_path, default={})

    selected = selection.get("selected_suggestions", [])
    selected_ids = selection.get("selected_ids", [])

    # safety switches
    apply_changes = os.getenv("CODERUNNERX_APPLY_AGENT_IMPROVEMENTS", "false").lower() == "true"
    dry_run = os.getenv("CODERUNNERX_DRY_RUN", "true").lower() == "true"

    actions = []
    ok = True

    if not selected:
        summary = "No selected improvements found. Nothing to implement."
    else:
        summary = f"Loaded {len(selected)} selected improvements: {selected_ids}"

        # IMPORTANT: This is where you implement your real patching logic.
        # For now: just record what would be applied.
        for s in selected:
            actions.append({
                "id": s.get("id"),
                "title": s.get("title"),
                "would_apply": True,
                "applied": False,
            })

        if apply_changes and not dry_run:
            # TODO: apply actual patches here
            # actions[i]["applied"] = True once applied
            summary += " (apply mode enabled, but no patch logic implemented yet)"
        else:
            summary += " (dry-run / apply disabled)"

    report = AgentReport(
        agent_name="implementer",
        run_id=run_id,
        created_at=time.time(),
        ok=ok,
        summary=summary,
        data={
            "selection_file": str(selection_path),
            "selected_ids": selected_ids,
            "selected_suggestions": selected,
            "apply_changes": apply_changes,
            "dry_run": dry_run,
            "actions": actions,
        },
        artifacts=[],
    )
    return write_report(report)

if __name__ == "__main__":
    out = run()
    log(f"Wrote report: {out}")
