from __future__ import annotations

from pathlib import Path
import time

from Agent.Working_Agents.base import (
    AgentReport,
    new_run_id,
    write_report,
    read_latest_report,
    run_child,
    REPO_ROOT,
)

from Agent.Working_Agents.support_functions.supervisor_support import (
    show_report_highlights,
    ask_run_next_agent,
    summarize_inventory
)

from Agent.Working_Agents.support_functions.all_agent_helper import (
    write_json,
    select_many_csv,
)


def run() -> Path:
    run_id = new_run_id("supervisor")

    # 0) inventory
    rc_inv = run_child("Agent.agents.inventory_agent")
    inventory = read_latest_report("inventory")

    # 1) scan
    rc_scan = run_child("Agent.agents.scanner_agent")
    scan = read_latest_report("scanner")

    # 2) fix
    rc_fix = run_child("Agent.agents.fixer_agent")
    fix = read_latest_report("fixer")

    # --- ask which suggestions to apply ---
    suggestions = []
    if fix and isinstance(fix, dict):
        data = fix.get("data", {})
        if isinstance(data, dict) and isinstance(data.get("suggestions"), list):
            suggestions = data["suggestions"]

    if not suggestions:
        suggestions = [
            {"id": 1, "title": "Improve scanner batching"},
            {"id": 2, "title": "Cache renderer surfaces"},
            {"id": 3, "title": "Tighten fixer prompt"},
        ]

    print("\nSuggested agent changes:")
    for s in suggestions:
        print(f"{s['id']}) {s['title']}")

    valid = {s["id"] for s in suggestions}
    selected_ids = select_many_csv("\nSelect (e.g. 1,3 or 0 for none): ", valid_numbers=valid)

    # IMPORTANT:
    # If your select_many_csv helper already treats "0" as none => you can delete this block.
    if selected_ids == [0]:
        selected_ids = []

    selected = [s for s in suggestions if s["id"] in selected_ids]

    selection_path = REPO_ROOT / "Agent" / "selected_agent_improvements.json"
    write_json(
        selection_path,
        {
            "run_id": run_id,
            "created_at": time.time(),
            "selected_ids": selected_ids,
            "selected_suggestions": selected,
        },
    )
    print("\nSaved selection to:", selection_path)

    # 3) smoke test
    rc_test = run_child("Agent.agents.smoke_test_agent")
    test = read_latest_report("smoke_test")

    ok = all([rc_inv == 0, rc_scan == 0, rc_fix == 0, rc_test == 0]) and bool(test and test.get("ok", False))
    summary = "Supervisor pipeline complete." if ok else "Supervisor pipeline complete: smoke test failed."

    # ---- SHOW HIGHLIGHTS + ASK BEFORE FINAL WRITE ----
    show_report_highlights(inventory, scan, fix, test, selected_ids)

    next_choice = ask_run_next_agent()
    rc_next = None
    if next_choice == 1:
        rc_next = run_child("Agent.agents.implementer_agent")
    # -------------------------------------------------

    report_data = {
        "child_return_codes": {
            "inventory": rc_inv,
            "scan": rc_scan,
            "fix": rc_fix,
            "smoke_test": rc_test,
        },
        "inventory": inventory,
        "scanner": scan,
        "fixer": fix,
        "smoke_test": test,
        "selected_improvement_ids": selected_ids,
        "selected_improvements": selected,
        "selection_file": str(selection_path),
        "next_agent_choice": next_choice,
        "next_agent_return_code": rc_next,
    }

    report = AgentReport(
        agent_name="supervisor",
        run_id=run_id,
        created_at=time.time(),
        ok=ok,
        summary=summary,
        data=report_data,
        artifacts=[str(selection_path)],
    )
    return write_report(report)


if __name__ == "__main__":
    out = run()
    print("Wrote report:", out)
