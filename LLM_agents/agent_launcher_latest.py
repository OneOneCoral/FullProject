"""
agent_launcher_latest.py

Unified "most recent" agent runner / launcher.

Based on the two variants you shared:
- 20251220_agent_launcher.py (simpler, strict -m run)
- runner.py (adds diagnostics, sys.path fix, module fallback, stronger error handling)

This version keeps the nicer diagnostics + fallback behavior, and also resolves the
"Agent vs agents" package-name mismatch by trying multiple import paths per agent.
"""

from __future__ import annotations

import os
import sys
import traceback
import subprocess
from pathlib import Path
import importlib.util
from typing import Dict, Optional, Tuple

from dotenv import load_dotenv


# -------------------------
# Setup
# -------------------------
# Single source of truth: repo root is the folder containing this file's parent (adjust if needed).
REPO_ROOT = Path(__file__).resolve().parents[1] if (Path(__file__).resolve().parent.name.lower() in {"agents", "agent"}) else Path(__file__).resolve().parent

# Ensure repo root is importable (important for find_spec and -m)
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

def _load_env() -> None:
    """
    Load .env from best-known locations.
    Priority:
      1) REPO_ROOT/.env
      2) REPO_ROOT/agents/PromtAgents/.env
      3) current working directory default behavior
    """
    candidates = [
        REPO_ROOT / ".env",
        REPO_ROOT / "agents" / "PromtAgents" / ".env",
    ]
    for p in candidates:
        if p.exists() and p.is_file():
            load_dotenv(p)
            print(f"Loaded .env from: {p}")
            return
    # Fall back: load_dotenv() will try CWD/.env
    load_dotenv()
    print("Loaded .env using default search (CWD/.env if present).")

_load_env()


# -------------------------
# Dynamic Agent Map
# -------------------------
def get_agents() -> Dict[str, Tuple[str, ...]]:
    """
    Map display_name -> tuple of candidate module import paths.
    We try multiple candidates to handle 'Agent' vs 'agents' vs flat packages.
    """
    return {
        "scanner": (
            "Agent.PromtAgents.20251220_scanner_agent",
            "agents.PromtAgents.20251220_scanner_agent",
            "PromtAgents.20251220_scanner_agent",
        ),
        "test_prompt": (
            "Agent.PromtAgents.20251220_test_prompt_agent",
            "agents.PromtAgents.20251220_test_prompt_agent",
            "PromtAgents.20251220_test_prompt_agent",
        ),
        "create_file_test": (
            "Agent.NonPromtAgents.create_file_test",
            "agents.NonPromtAgents.create_file_test",
            "NonPromtAgents.create_file_test",
        ),
    }


def module_spec(module_path: str):
    try:
        return importlib.util.find_spec(module_path)
    except Exception:
        return None


def module_exists(module_path: str) -> bool:
    return module_spec(module_path) is not None


def module_file_path(module_path: str) -> Optional[Path]:
    """
    If module is importable, return its file path (spec.origin).
    For packages, origin may be __init__.py.
    """
    spec = module_spec(module_path)
    if not spec or not getattr(spec, "origin", None):
        return None
    return Path(spec.origin)


def resolve_agent_module(candidates: Tuple[str, ...]) -> Optional[str]:
    for mod in candidates:
        if module_exists(mod):
            return mod
    return None


def validate_agents(agent_map: Dict[str, Tuple[str, ...]]) -> Tuple[Dict[str, str], Dict[str, Tuple[str, ...]]]:
    """
    Returns (valid_agents, missing_agents)
      valid_agents: display_name -> resolved_module
      missing_agents: display_name -> candidate_modules
    """
    valid: Dict[str, str] = {}
    missing: Dict[str, Tuple[str, ...]] = {}
    for name, candidates in agent_map.items():
        resolved = resolve_agent_module(candidates)
        if resolved:
            valid[name] = resolved
        else:
            missing[name] = candidates
    return valid, missing


def choose_agent(agent_map: Dict[str, str]) -> str:
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


def print_diagnostics() -> None:
    print("\n--- Diagnostics ---")
    print("Python:", sys.executable)
    print("CWD:", os.getcwd())
    print("REPO_ROOT:", REPO_ROOT)
    print("REPO_ROOT exists:", REPO_ROOT.exists())
    print("sys.path[0:8]:", sys.path[:8])
    print("CODERUNNERX_DRY_RUN:", os.getenv("CODERUNNERX_DRY_RUN"))
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

    path = module_file_path(mod)
    if path and path.exists() and path.suffix == ".py":
        print(f"\n⚠ -m failed (code={r.returncode}). Fallback: run file directly: {path}")
        r2 = subprocess.run([sys.executable, str(path)], cwd=str(REPO_ROOT), env=env)
        return r2.returncode

    print(f"\n❌ -m failed (code={r.returncode}) and no runnable file path found for: {mod}")
    return r.returncode


def main() -> None:
    try:
        print("Launcher starting...")
        print_diagnostics()

        agents = get_agents()
        valid_agents, missing_agents = validate_agents(agents)

        if missing_agents:
            print("⚠ Missing agents (module not found). Tried these candidates:")
            for name, mods in missing_agents.items():
                print(f"  - {name}:")
                for m in mods:
                    print(f"      {m}")

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
        print("\n❌ Launcher crashed with exception:\n")
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
