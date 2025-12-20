import sys
import subprocess
from pathlib import Path
import importlib
import pkgutil

from dotenv import load_dotenv
import os
from Agent.core.base import is_dry_run
# -------------------------
# Setup
# -------------------------
REPO_ROOT = Path(__file__).resolve().parent  # adjust if needed
ENV_PATH = REPO_ROOT / "agents" / "PromtAgents" / ".env"
load_dotenv(ENV_PATH)

# -------------------------
# Dynamic Agent Discovery
# -------------------------
def discover_agents():
    agent_modules = {}

    base_packages = [
        ("agents.Working_Agents", REPO_ROOT / "agents" / "Working_Agents"),
        ("agents.PromtAgents", REPO_ROOT / "agents" / "PromtAgents"),
        ("agents.NonPromtAgents", REPO_ROOT / "agents" / "NonPromtAgents"),
    ]

    for base_name, path in base_packages:
        if not path.exists():
            continue

        for _, name, _ in pkgutil.iter_modules([str(path)]):
            # You can pick your convention here:
            # - suffix: _agent
            # - prefix: agent_
            # - any .py file
            if name.endswith("_agent") or name.endswith("_test") or name.startswith("create_"):
                full_name = f"{base_name}.{name}"
                agent_modules[name] = full_name

    return dict(sorted(agent_modules.items(), key=lambda kv: kv[0].lower()))


def choose_agent(agent_map):
    print("\nSelect an agent to run:\n")
    for i, name in enumerate(agent_map.keys(), 1):
        print(f"  {i}) {name}")

    choice = input("\nAgent> ").strip()
    if choice.isdigit():
        idx = int(choice)
        if 1 <= idx <= len(agent_map):
            return list(agent_map.keys())[idx - 1]
    elif choice in agent_map:
        return choice
    print("Invalid choice. Exiting.")
    sys.exit(1)


def main():
    agents = discover_agents()
    if not agents:
        print("No agents found.")
        sys.exit(1)

    # Ask once, force y/n
    ans = input("Run in DRY_RUN mode? [y/n]: ").strip().lower()
    while ans not in {"y", "n"}:
        ans = input("Please enter y or n: ").strip().lower()

    dry_run = (ans == "y")

    # Choose agent
    selected = choose_agent(agents)
    mod = agents[selected]

    # Build child env and set DRY_RUN explicitly
    env = os.environ.copy()
    env["CODERUNNERX_DRY_RUN"] = "true" if dry_run else "false"

    print(f"\n▶ Running agent: {selected}")
    print(f"  module: {mod}")
    print(f"  CODERUNNERX_DRY_RUN={env['CODERUNNERX_DRY_RUN']}\n")

    result = subprocess.run(
        [sys.executable, "-m", mod],
        cwd=str(REPO_ROOT),
        env=env,
    )
    sys.exit(result.returncode)


if __name__ == "__main__":
    main()
