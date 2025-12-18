from __future__ import annotations

from typing import Any, Dict, List, Optional


def show_report_highlights(
    inventory: Optional[Dict[str, Any]],
    scanner: Optional[Dict[str, Any]],
    fixer: Optional[Dict[str, Any]],
    smoke_test: Optional[Dict[str, Any]],
    selected_ids: List[int],
) -> None:
    print("\n================ REPORT HIGHLIGHTS ================")

    if inventory and isinstance(inventory, dict):
        count = inventory.get("data", {}).get("count")
        if count is not None:
            print(f"- Inventory: indexed files = {count}")

    if scanner:
        print("- Scanner: report loaded")

    if fixer and isinstance(fixer, dict):
        sugg = fixer.get("data", {}).get("suggestions")
        if isinstance(sugg, list):
            print(f"- Fixer: suggestions available = {len(sugg)}")
            print(f"- You selected suggestion IDs: {selected_ids}")

    if smoke_test and isinstance(smoke_test, dict):
        ok = smoke_test.get("ok", False)
        print(f"- Smoke test: ok = {ok}")

    print("===================================================\n")


def ask_run_next_agent() -> int:
    print("Target an implementer with this report?")
    print("1) Yes: run implementer_agent now")
    print("0) No: finish")
    choice = input("Select: ")

    if not choice.isdigit():
        return 0
    return int(choice)

def summarize_inventory(inventory: dict, max_files: int = 10) -> None:
    if not inventory or not isinstance(inventory, dict):
        print("- Inventory: no report")
        return

    data = inventory.get("data", {})
    count = data.get("count")
    index = data.get("index", [])

    print(f"\nInventory summary:")
    print(f"- Files indexed: {count}")
    print(f"- Showing first {min(max_files, len(index))} files:")

    for i, entry in enumerate(index[:max_files], start=1):
        f = entry.get("file", "?")
        funcs = entry.get("functions", [])
        classes = entry.get("classes", [])
        print(f"  {i}) {f}")
        print(f"     functions: {len(funcs)} | classes: {len(classes)}")