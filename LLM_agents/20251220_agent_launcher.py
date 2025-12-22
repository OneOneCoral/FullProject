import sys
import subprocess
from pathlib import Path
import importlib.util
from dotenv import load_dotenv
import os

# -------------------------
# Setup
# -------------------------
REPO_ROOT = Path(__file__).resolve().parents[1]  #single source of truth
ENV_PATH = REPO_ROOT / "agents" / "PromtAgents" / ".env"
load_dotenv(ENV_PATH)

# -------------------------
# Dynamic Agent
# -------------------------
def get_agents():
    # map display_name -> module path
    return {
        "scanner": "Agent.PromtAgents.20251220_scanner_agent",
        "test_prompt": "agents.PromtAgents.20251220_test_prompt_agent",
        "create_file_test": "agents.NonPromtAgents.create_file_test",
    }

def module_exists(module_path: str) -> bool:
    # Checks if Python can resolve the module (file/package exists and is importable)
    return importlib.util.find_spec(module_path) is not None

def validate_agents(agent_map: dict[str, str]) -> tuple[dict[str, str], dict[str, str]]:
    """
    Returns (valid_agents, missing_agents) where missing_agents is a dict of name->module
    for anything that can't be resolved.
    """
    valid = {}
    missing = {}
    for name, mod in agent_map.items():
        if module_exists(mod):
            valid[name] = mod
        else:
            missing[name] = mod
    return valid, missing

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
    agents = get_agents()

    valid_agents, missing_agents = validate_agents(agents)

    if missing_agents:
        print("\n⚠ Missing agents (module not found):")
        for name, mod in missing_agents.items():
            print(f"  - {name}: {mod}")

    if not valid_agents:
        print("\nNo valid agents found. Exiting.")
        sys.exit(1)

    # Ask once, force y/n
    ans = input("\nRun in DRY_RUN mode? [y/n]: ").strip().lower()
    while ans not in {"y", "n"}:
        ans = input("Please enter y or n: ").strip().lower()

    dry_run = (ans == "y")

    # Choose agent (only from valid ones)
    selected = choose_agent(valid_agents)
    mod = valid_agents[selected]

    # Final safety check right before running
    if not module_exists(mod):
        print(f"\n❌ Selected agent '{selected}' is missing now: {mod}")
        sys.exit(1)

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