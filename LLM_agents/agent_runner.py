import sys
import subprocess
from pathlib import Path
import importlib.util
from dotenv import load_dotenv
import os
import traceback

print("HI")

# -------------------------
# Setup
# -------------------------
REPO_ROOT = Path(__file__).resolve().parent

# load .env correctly (file path, not directory)
ENV_FILE = REPO_ROOT / ".env"
if ENV_FILE.exists():
    load_dotenv(REPO_ROOT / ".env")

# Ensure repo root is importable
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

# ALSO ensure agent_list is importable (so Agent.* inside agent_list can work)
AGENT_LIST_ROOT = REPO_ROOT / "agent_list"
if AGENT_LIST_ROOT.exists() and str(AGENT_LIST_ROOT) not in sys.path:
    sys.path.insert(0, str(AGENT_LIST_ROOT))

# -------------------------
# Dynamic Agent Discovery
# -------------------------
def get_agents():
    """
    Scan agent_list and return a list of .py file paths.
    """
    agents = []
    search_folders = [REPO_ROOT / "agent_list"]

    for folder in search_folders:
        if not folder.exists():
            continue

        for py in folder.rglob("*.py"):
            if py.name.startswith("_") or py.name == "__init__.py":
                continue
            agents.append(py)

    return agents

def pyfile_to_module(py_file: Path, repo_root: Path) -> str:
    """
    Convert a .py path under repo_root into a python module string.
    Example:
      repo_root/agent_list/NonPromtAgents/x.py -> agent_list.NonPromtAgents.x
    """
    py_file = py_file.resolve()
    repo_root = repo_root.resolve()
    rel = py_file.relative_to(repo_root).with_suffix("")
    return ".".join(rel.parts)

def module_to_file_path(module_path: str) -> Path | None:
    """
    If module is importable, return its file path (spec.origin).
    """
    try:
        spec = importlib.util.find_spec(module_path)
    except Exception:
        return None
    if not spec or not getattr(spec, "origin", None):
        return None
    return Path(spec.origin)

def choose_agent(agent_list):
    print("\nSelect an agent to run:\n")
    for idx, agent in enumerate(agent_list, start=1):
        print(f"{idx}. {agent.stem}")

    choice = input("\nAgent> ").strip()

    if choice.isdigit():
        idx = int(choice)
        if 1 <= idx <= len(agent_list):
            return agent_list[idx - 1]
    else:
        for agent in agent_list:
            if choice == agent.stem:
                return agent

    print("Invalid choice. Exiting.")
    sys.exit(1)

def print_diagnostics():
    print("\n--- Diagnostics ---")
    print("Python:", sys.executable)
    print("CWD:", os.getcwd())
    print("REPO_ROOT:", REPO_ROOT)
    print("REPO_ROOT exists:", REPO_ROOT.exists())
    print("ENV_FILE:", ENV_FILE)
    print("ENV_FILE exists:", ENV_FILE.exists())
    print("AGENT_LIST_ROOT:", AGENT_LIST_ROOT)
    print("AGENT_LIST_ROOT exists:", AGENT_LIST_ROOT.exists())
    print("sys.path[0:8]:", sys.path[:8])
    print("-------------------\n")

def run_module_with_fallback(mod: str, env: dict) -> int:
    """
    Try: python -m <module>
    If that fails and we can resolve a file path, fall back to running the file directly.
    """
    print(f"Launching via -m: {mod}")
    r = subprocess.run([sys.executable, "-m", mod], cwd=str(REPO_ROOT), env=env)
    if r.returncode == 0:
        return 0

    path = module_to_file_path(mod)
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
        if not agents:
            print("❌ No agents found under agent_list/. Exiting.")
            sys.exit(1)

        ans = input("Run in DRY_RUN mode? [y/n]: ").strip().lower()
        while ans not in {"y", "n"}:
            ans = input("Please enter y or n: ").strip().lower()
        dry_run = (ans == "y")

        selected = choose_agent(agents)
        mod = pyfile_to_module(selected, REPO_ROOT)

        # validate module is importable before running -m
        if importlib.util.find_spec(mod) is None:
            print(f"\n⚠ Module not importable via -m: {mod}")
            print("   (This usually means missing __init__.py in a package folder.)")
            print("   Will still try fallback to running the file directly.\n")

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
