from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional
import json


# -----------------------------
# Basic logging
# -----------------------------
def log(msg: str) -> None:
    print(msg, flush=True)


# -----------------------------
# JSON helpers
# -----------------------------
def read_json(path: Path, default: Optional[dict] = None) -> dict:
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return default or {}


def write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")


# -----------------------------
# Selection helpers (NO strip)
# -----------------------------
def select_one_number(prompt: str, valid_numbers: set[int], allow_zero: bool = True) -> Optional[int]:
    """
    Read ONE number from input.
    No .strip(). If user types spaces, it's invalid.
    Returns:
      - None invalid
      - 0 if allow_zero and user entered 0
      - valid number otherwise
    """
    choice = input(prompt)

    if not choice.isdigit():
        return None

    n = int(choice)

    if allow_zero and n == 0:
        return 0

    if n in valid_numbers:
        return n

    return None


def select_many_csv(prompt: str, valid_numbers: set[int], allow_zero: bool = True) -> List[int]:
    """
    Read CSV like: 1,3,5
    No .strip(). So "1, 3" -> " 3" is invalid.
    If allow_zero and user enters "0" => returns [] (meaning none).
    """
    choice = input(prompt)

    # single number quick path
    if choice.isdigit():
        n = int(choice)
        if allow_zero and n == 0:
            return []
        return [n] if n in valid_numbers else []

    parts = choice.split(",")
    out: List[int] = []
    for p in parts:
        if p.isdigit():
            n = int(p)
            if allow_zero and n == 0:
                # if user included 0 anywhere, treat as "none"
                return []
            if n in valid_numbers:
                out.append(n)
    return out


# -----------------------------
# Pretty printing (Supervisor or any agent)
# -----------------------------
def print_suggestions(suggestions: List[Dict[str, Any]]) -> None:
    print("\nSuggested changes:")
    for s in suggestions:
        sid = s.get("id", "?")
        title = s.get("title") or s.get("summary") or str(s)
        print(f"{sid}) {title}")


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


def ask_run_implementer() -> int:
    print("Target an implementer with this report?")
    print("1) Yes: run implementer_agent now")
    print("0) No: finish")
    choice = input("Select: ")

    if not choice.isdigit():
        return 0
    return int(choice)

def discover_agents():
    """
    Discover agent modules under Agent/Working_Agents that end with *_agent.py
    and return {cli_name: module_path}.
    """
    agents_dir = REPO_ROOT / "Agent" / "Working_Agents"
    if not agents_dir.exists():
        raise SystemExit(f"Agents directory not found: {agents_dir}")

    agents = {}
    for file in agents_dir.glob("*_agent.py"):
        module_stem = file.stem  # e.g. inventory_agent
        cli_name = module_stem[:-6] if module_stem.endswith("_agent") else module_stem
        module_path = f"Agent.Working_Agents.{module_stem}"
        agents[cli_name] = module_path

    return dict(sorted(agents.items(), key=lambda x: x[0].lower()))


def print_menu(agent_names):
    print("\nSelect an agent to run:\n")
    for i, name in enumerate(agent_names, start=1):
        print(f"  {i:>2}) {name}")
    print("\nType a number (e.g. 1) or a name (e.g. scanner).")
    print("Type q to quit.\n")


def choose_agent(agent_names):
    while True:
        choice = input("Agent> ").strip()
        if choice.lower() in ("q", "quit", "exit"):
            raise SystemExit(0)

        if choice.isdigit():
            idx = int(choice)
            if 1 <= idx <= len(agent_names):
                return agent_names[idx - 1]
            print("Invalid number. Try again.")
            continue

        if choice in agent_names:
            return choice

        matches = [n for n in agent_names if choice.lower() in n.lower()]
        if matches:
            print("Did you mean one of these?")
            for m in matches:
                print(" -", m)
        else:
            print("Unknown agent. Try again.")


def run_module(module_path: str) -> int:
    # Run as a module so package imports work
    proc = subprocess.run(
        [sys.executable, "-m", module_path],
        cwd=str(REPO_ROOT),
        check=False,
    )
    return proc.returncode


def main():
    agents = discover_agents()
    if not agents:
        print("No agents found in Agent/Working_Agents (expected *_agent.py).")
        return 2

    # Direct mode: python Agent/run_agent.py scanner
    if len(sys.argv) >= 2:
        name = sys.argv[1]
        if name not in agents:
            print("Unknown agent:", name)
            print("Available:", ", ".join(agents.keys()))
            return 2
        return run_module(agents[name])

    # Interactive mode
    names = list(agents.keys())
    print_menu(names)
    selected = choose_agent(names)
    print(f"\nRunning: {selected}\n")
    return run_module(agents[selected])


if __name__ == "__main__":
    raise SystemExit(main())