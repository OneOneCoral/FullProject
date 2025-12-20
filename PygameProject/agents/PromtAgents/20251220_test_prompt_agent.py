from __future__ import annotations
import json
import os
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dotenv import load_dotenv
from openai import OpenAI

from Agent.core.base import REPO_ROOT, AgentReport, write_report, run_child

# -------------------------
# Config and .env loading
# -------------------------

# Get this script's location (e.g. .../agents/PromtAgents)
SCRIPT_DIR = Path(__file__).parent

# Set .env path in same folder as this script
ENV_PATH = SCRIPT_DIR / ".env"

# Load it
load_dotenv(ENV_PATH)
print(f"Loaded .env from: {ENV_PATH}")

# Check values
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise SystemExit("Missing OPENAI_API_KEY. Is your .env file in the same folder as this script?")

print(" OPENAI_API_KEY loaded")

# Safety: start in DRY_RUN so you can inspect diffs before writing.
DRY_RUN = os.getenv("CODERUNNERX_DRY_RUN", "false").lower() in ("1", "true", "yes")

# Restrict what the AI is allowed to modify (minimize blast radius).
# Add your real entrypoint once you find it (e.g., "Agent/main.py" or "src/main.py").
ALLOWED_EDIT_PATH_SUFFIXES = [
    "main.py", "game.py", "app.py", "run.py",
]

# If you want the agent to be able to "improve itself", you can allow edits inside Agent/
# but ONLY after you've tested safely. Leave False for now.
ALLOW_SELF_EDIT = os.getenv("twst_prompt_agent_ALLOW_SELF_EDIT", "false").lower() in ("1", "true", "yes")

# Optional: allow edits to agent code (still constrained)
SELF_EDIT_SUFFIXES = ["Agent/20251220_test_prompt_agent.py"]

MODEL = os.getenv("CODERUNNERX_MODEL", "gpt-4.1")

client = OpenAI(api_key=OPENAI_API_KEY)


# -------------------------
# Utilities
# -------------------------

def load_python_files(repo_root: Path) -> Dict[str, str]:
    files: Dict[str, str] = {}
    for p in repo_root.rglob("*.py"):
        s = str(p)
        if any(x in s for x in ["/.git/", "\\.git\\", "/venv/", "\\venv\\", "__pycache__"]):
            continue
        try:
            files[s] = p.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
    return files


def is_allowed_to_edit(path: str) -> bool:
    p = Path(path).resolve()

    # always require edits to be inside repo
    try:
        p.relative_to(REPO_ROOT.resolve())
    except ValueError:
        return False

    # allow root main.py explicitly
    if p == (REPO_ROOT / "main.py").resolve():
        return True

    # allow by filename suffix list
    return p.name in ALLOWED_EDIT_PATH_SUFFIXES

def write_file(path: str, content: str) -> None:
    p = Path(path)
    p.write_text(content, encoding="utf-8")


def run_cmd(cmd: List[str], cwd: Path) -> Tuple[int, str]:
    try:
        proc = subprocess.run(cmd, cwd=str(cwd), capture_output=True, text=True, check=False)
        out = (proc.stdout or "") + ("\n" + proc.stderr if proc.stderr else "")
        return proc.returncode, out.strip()
    except Exception as e:
        return 999, str(e)


# -------------------------
# Multi-agent framework (minimal)
# -------------------------

@dataclass
class RepoContext:
    repo_root: Path
    files: Dict[str, str]
    notes: List[str]


@dataclass
class Change:
    path: str
    summary: str
    updated_code: str


class Agent:
    name: str = "agent"

    def run(self, ctx: RepoContext) -> Tuple[RepoContext, List[Change]]:
        raise NotImplementedError




    def run(self, ctx: RepoContext) -> Tuple[RepoContext, List[Change]]:
        # Keep the scan small: file list + a few likely candidates’ content (if present)
        paths = sorted(ctx.files.keys())
        likely = [p for p in paths if p.endswith(("main.py", "game.py", "app.py", "run.py"))]
        bundle = {
            "repo_root": str(ctx.repo_root),
            "python_files_count": len(paths),
            "python_files": paths[:400],  # cap
            "likely_candidates": {p: ctx.files[p][:4000] for p in likely[:10]}  # cap per file
        }

        resp = client.responses.create(
            model=MODEL,
            input=[
                {"role": "system", "content": self.SYSTEM},
                {"role": "user", "content": json.dumps(bundle)},
            ],
        )
        data = json.loads(resp.output_text)

        entrypoints = data.get("entrypoints", [])
        notes = data.get("notes", [])
        targets = data.get("recommended_edit_targets", [])

        ctx.notes.append(f"[scanner] entrypoints={entrypoints}")
        for n in notes:
            ctx.notes.append(f"[scanner] {n}")

        # Update allowlist dynamically: if scanner found a better target, allow it (still safe)
        # (You can remove this if you want strict manual allowlist.)
        for t in targets:
            if isinstance(t, str) and t.endswith(".py"):
                suf = t.split("/")[-1]
                if suf not in ALLOWED_EDIT_PATH_SUFFIXES:
                    ALLOWED_EDIT_PATH_SUFFIXES.append(suf)

        return ctx, []


# -------------------------
# Orchestrator
# -------------------------

def apply_changes(changes: List[Change], ctx: RepoContext) -> None:
    if not changes:
        print("No changes proposed.")
        return

    print("\nProposed changes:")
    for c in changes:
        print(f"- {c.path}: {c.summary}")

    if DRY_RUN:
        print("\nDRY_RUN=true -> Not writing files. Set CODERUNNERX_DRY_RUN=false to apply.")
        return

    for c in changes:
        if not is_allowed_to_edit(c.path):
            print(f"[skip] not allowed to edit: {c.path}")
            continue
        write_file(c.path, c.updated_code)
        # update ctx cache
        ctx.files[c.path] = c.updated_code
        print(f"[write] {c.path}")

    # Smoke compile check on allowed edits
    edited = [c.path for c in changes if is_allowed_to_edit(c.path)]
    for p in edited:
        rc, out = run_cmd(["python", "-m", "py_compile", p], cwd=ctx.repo_root)
        if rc != 0:
            print(f"[py_compile FAIL] {p}\n{out}\n")
        else:
            print(f"[py_compile OK] {p}")


def main() -> None:
    print("Repo root seen by agent:", REPO_ROOT)
    print("DRY_RUN:", DRY_RUN)
    print("ALLOW_SELF_EDIT:", ALLOW_SELF_EDIT)

    files = load_python_files(REPO_ROOT)
    ctx = RepoContext(repo_root=REPO_ROOT, files=files, notes=[])

    agents: List[Agent] = [
        ScannerAgent(),
        EntrypointAgent(),
        FixerAgent(),
        SmokeTestAgent(),
        SelfImproveAgent(),
    ]

    all_changes: List[Change] = []
    for a in agents:
        ctx, changes = a.run(ctx)
        if changes:
            all_changes.extend(changes)

    apply_changes(all_changes, ctx)

    print("\nNotes:")
    for n in ctx.notes[-30:]:
        print("-", n)


if __name__ == "__main__":
    main()