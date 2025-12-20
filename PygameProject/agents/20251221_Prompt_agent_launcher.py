import sys
import subprocess
from pathlib import Path
import importlib
import pkgutil

from dotenv import load_dotenv

# -------------------------
# Setup
# -------------------------
REPO_ROOT = Path(__file__).resolve().parents[1]  # adjust if needed
ENV_PATH = REPO_ROOT / "agents" / "PromtAgents" / ".env"
load_dotenv(ENV_PATH)

# -------------------------
# Dynamic Agent Discovery
# -------------------------

def discover_agents():
    agent_modules = {}
    base_packages = [
        ("agents.Working_Agents", REPO_ROOT / "agents" / "Working_Agents"),
        ("agents.PromtAgents", REPO_ROOT / "agents" / "PromtAgents")
    ]
    for base_name, path in base_packages:
        for finder, name, ispkg in pkgutil.iter_modules([str(path)]):
            if name.endswith("_agent"):
                full_name = f"{base_name}.{name}"
                agent_modules[name] = full_name
    return agent_modules


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

    selected = choose_agent(agents)
    mod = agents[selected]
    print(f"\n▶ Running agent: {selected}\n")
    result = subprocess.run([sys.executable, "-m", mod], cwd=str(REPO_ROOT))
    sys.exit(result.returncode)


if __name__ == "__main__":
    main()
