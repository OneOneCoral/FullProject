import sys
import subprocess
from pathlib import Path
import importlib.util
from dotenv import load_dotenv
import os
import traceback

print ("HI")
# -------------------------
# Setup
# -------------------------
REPO_ROOT = Path(__file__).resolve().parent  # adjust if needed
ENV_PATH = REPO_ROOT
load_dotenv(ENV_PATH)

# Ensure repo root is importable (important for find_spec and -m)
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

AGENTLIST = []
# -------------------------
# Dynamic Agent
# -------------------------
def get_agents():
    # IMPORTANT: pick ONE package name and stick to it: "agents" OR "Agent"
    # This example assumes your folder is named: agents/
    return {
        "scanner": "PromtAgents.20251220_scanner_agent",
        "test_prompt": "PromtAgents.20251220_test_prompt_agent",
        "create_file_test": "NonPromtAgents.create_file_test",
    }


def module_spec(module_path: str):
    try:
        return importlib.util.find_spec(module_path)
    except Exception:
        return None


def module_exists(module_path: str) -> bool:
    return module_spec(module_path) is not None


def module_file_path(module_path: str) -> Path | None:
    """
    If module is importable, return its file path (spec.origin).
    """
    spec = module_spec(module_path)
    if not spec or not getattr(spec, "origin", None):
        return None
    # For packages, origin can be __init__.py; that's still runnable only via -m.
    return Path(spec.origin)


def validate_agents(agent_map: dict[str, str]) -> tuple[dict[str, str], dict[str, str]]:
    valid, missing = {}, {}
    for name, i in agent_map.items():
        if module_exists(i):
            valid[name] = i
        else:
            missing[name] = i
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


def print_diagnostics():
    print("\n--- Diagnostics ---")
    print("Python:", sys.executable)
    print("CWD:", os.getcwd())
    print("REPO_ROOT:", REPO_ROOT)
    print("REPO_ROOT exists:", REPO_ROOT.exists())
    print("ENV_PATH:", ENV_PATH)
    print("ENV_PATH exists:", ENV_PATH.exists())
    print("sys.path[0:5]:", sys.path[:5])
    print("-------------------\n")


def run_module_with_fallback(mod: str, env: dict) -> int:
    """
    Try: python -m <module>
    If that fails and we can resolve a file path, fall back to running the file directly.
    """
    # 1) Normal way
    print(f"Launching via -m: {mod}")
    r = subprocess.run([sys.executable, "-m", mod], cwd=str(REPO_ROOT), env=env)
    if r.returncode == 0:
        return 0

    # 2) Fallback: direct file execution
    path = module_file_path(mod)
    if path and path.exists() and path.suffix == ".py":
        print(f"\n⚠ -m failed (code={r.returncode}). Fallback: run file directly: {path}")
        r2 = subprocess.run([sys.executable, str(path)], cwd=str(REPO_ROOT), env=env)
        return r2.returncode

    print(f"\n❌ -m failed (code={r.returncode}) and no runnable file path found for: {mod}")
    return r.returncode


def main():
    try:
        print("Runner starting...")
        print_diagnostics()

        agents = get_agents()
        valid_agents, missing_agents = validate_agents(agents)

        if missing_agents:
            print("⚠ Missing agents (module not found):")
            for name, mod in missing_agents.items():
                print(f"  - {name}: {mod}")

        if not valid_agents:
            print("\n❌ No valid agents found. Exiting.")
            sys.exit(1)

        ans = input("Run in DRY_RUN mode? [y/n]: ").strip().lower()
        while ans not in {"y", "n"}:
            ans = input("Please enter y or n: ").strip().lower()
        dry_run = (ans == "y")

        selected = choose_agent(valid_agents)
        mod = valid_agents[selected]

        # Final safety check right before running
        if not module_exists(mod):
            print(f"\n❌ Selected agent '{selected}' cannot be resolved now: {mod}")
            sys.exit(1)

        env = os.environ.copy()
        env["CODERUNNERX_DRY_RUN"] = "true" if dry_run else "false"

        print(f"\n▶ Running agent: {selected}")
        print(f"  module: {mod}")
        print(f"  CODERUNNERX_DRY_RUN={env['CODERUNNERX_DRY_RUN']}\n")

        code = run_module_with_fallback(mod, env)
        sys.exit(code)

    except KeyboardInterrupt:
        print("\nInterrupted.")
        sys.exit(130)
    except Exception:
        print("\n❌ Runner crashed with exception:\n")
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()