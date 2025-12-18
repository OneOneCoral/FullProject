from __future__ import annotations

import json
import os
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from dotenv import load_dotenv
from openai import OpenAI



# -------------------------
# Config
# -------------------------


REPO_ROOT = Path.cwd()  # MUST be repo root; set PyCharm Working Directory accordingly
AGENT_DIR = REPO_ROOT / "Agent"
ENV_PATH = AGENT_DIR / ".env"

load_dotenv(ENV_PATH)

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise SystemExit("Missing OPENAI_API_KEY. Put it in Agent/.env")

# Safety: start in DRY_RUN so you can inspect diffs before writing.
DRY_RUN = os.getenv("CODERUNNERX_DRY_RUN", "false").lower() in ("1", "true", "yes")

# Restrict what the AI is allowed to modify (minimize blast radius).
# Add your real entrypoint once you find it (e.g., "Agent/main.py" or "src/main.py").
ALLOWED_EDIT_PATH_SUFFIXES = [
    "main.py", "game.py", "app.py", "run.py",
]

# If you want the agent to be able to "improve itself", you can allow edits inside Agent/
# but ONLY after you've tested safely. Leave False for now.
ALLOW_SELF_EDIT = os.getenv("CODERUNNERX_ALLOW_SELF_EDIT", "false").lower() in ("1", "true", "yes")

# Optional: allow edits to agent code (still constrained)
SELF_EDIT_SUFFIXES = ["Agent/code_runner_x.py"]

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
    # allow repo-root main.py explicitly
    if path == str(REPO_ROOT / "main.py"):
        return True

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


class ScannerAgent(Agent):
    name = "scanner"

    SYSTEM = """You are CodeRunner-X Scanner for a Python Pygame repo.

Task:
- Identify the most likely entrypoint file(s) that should start the game.
- Identify where the main loop is or should be.
- Propose minimal fixes needed to get a working window + stable loop:
  pygame.init(), display.set_mode, event loop with QUIT, Clock tick.

Output MUST be strict JSON:
{
  "entrypoints": ["<path>", ...],
  "notes": ["...", "..."],
  "recommended_edit_targets": ["<path>", ...]
}
Return ONLY JSON.
"""

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


class EntrypointAgent(Agent):
    name = "entrypoint"

    SYSTEM = """You are CodeRunner-X Entrypoint Agent.

Goal:
- Create (or update) a repository-root main.py that runs a working Pygame main loop.
- You MUST base it on the best existing working entrypoint in the repo (prefer newest date).
- Keep it minimal and runnable.
- If there are shared classes (e.g. Game, Player, Engine), try importing and using them,
  but only if they import cleanly. Otherwise keep a minimal loop.

Output strict JSON:
{
  "path": "<absolute path to repo-root main.py>",
  "summary": "<1-2 sentences>",
  "updated_code": "<full file contents>"
}
Return ONLY JSON.
"""

    def run(self, ctx: RepoContext) -> Tuple[RepoContext, List[Change]]:
        target = str(ctx.repo_root / "main.py")
        existing = ctx.files.get(target, "")

        payload = {
            "repo_root": str(ctx.repo_root),
            "target_path": target,
            "target_exists": bool(existing),
            "target_code": existing,
            "scanner_notes": ctx.notes,
            "all_python_paths": sorted(list(ctx.files.keys())),
        }

        resp = client.responses.create(
            model=MODEL,
            input=[
                {"role": "system", "content": self.SYSTEM},
                {"role": "user", "content": json.dumps(payload)},
            ],
        )
        data = json.loads(resp.output_text)
        upd = data["updated_code"]
        return ctx, [Change(path=data["path"], summary=data.get("summary", ""), updated_code=upd)]


class FixerAgent(Agent):
    name = "fixer"

    SYSTEM = """You are CodeRunner-X Fixer for a Python Pygame repository.

Primary goal:
- Produce a working entrypoint that launches a window and runs a stable main loop:
  pygame.init()
  screen = pygame.display.set_mode(...)
  clock = pygame.time.Clock()
  while running:
    handle events (QUIT)
    update()
    draw()
    pygame.display.flip()
    clock.tick(60)
  pygame.quit()

Constraints:
- Minimal edits. Reuse existing Game/Engine classes if present.
- Fix imports and wiring only. Avoid big refactors.
- Do not add dependencies.
- If you are unsure, leave file unchanged.

Output MUST be strict JSON:
{
  "path": "<path>",
  "summary": "<1-2 sentences or 'no change'>",
  "updated_code": "<full file text>"
}
Return ONLY JSON.
"""

    def run(self, ctx: RepoContext) -> Tuple[RepoContext, List[Change]]:
        changes: List[Change] = []

        # Only attempt to fix files we allow
        for path, code in ctx.files.items():
            if not is_allowed_to_edit(path):
                continue

            payload = {
                "path": path,
                "repo_notes": ctx.notes[-20:],  # give the fixer recent context
                "code": code,
                "all_python_paths_sample": sorted(list(ctx.files.keys()))[:300],
            }

            resp = client.responses.create(
                model=MODEL,
                input=[
                    {"role": "system", "content": self.SYSTEM},
                    {"role": "user", "content": json.dumps(payload)},
                ],
            )

            data = json.loads(resp.output_text)
            upd = data["updated_code"]
            summary = data.get("summary", "")

            if upd != code:
                changes.append(Change(path=path, summary=summary, updated_code=upd))
            else:
                ctx.notes.append(f"[fixer] no change: {path}")

        return ctx, changes


class SelfImproveAgent(Agent):
    """
    Optional: lets the tool improve itself (e.g., better prompts, better allowlist logic).
    Keep disabled until you trust the workflow.
    """
    name = "self_improve"

    SYSTEM = """You are CodeRunner-X Self-Improve Agent.

Goal:
- Improve Agent/code_runner_x.py to make it safer and more effective:
  - better dry-run behavior
  - clearer logs
  - better target detection
  - safer constraints

Rules:
- Only modify Agent/code_runner_x.py
- Keep changes minimal and safe
- Output strict JSON {path, summary, updated_code}
Return ONLY JSON.
"""

    def run(self, ctx: RepoContext) -> Tuple[RepoContext, List[Change]]:
        if not ALLOW_SELF_EDIT:
            ctx.notes.append("[self_improve] disabled")
            return ctx, []

        target = str(AGENT_DIR / "code_runner_x.py")
        if target not in ctx.files:
            ctx.notes.append("[self_improve] target not found")
            return ctx, []

        payload = {"path": target, "code": ctx.files[target]}
        resp = client.responses.create(
            model=MODEL,
            input=[
                {"role": "system", "content": self.SYSTEM},
                {"role": "user", "content": json.dumps(payload)},
            ],
        )
        data = json.loads(resp.output_text)
        upd = data["updated_code"]
        if upd != ctx.files[target]:
            return ctx, [Change(path=target, summary=data.get("summary", ""), updated_code=upd)]
        return ctx, []


class SmokeTestAgent(Agent):
    name = "smoke_test"

    def run(self, ctx: RepoContext) -> Tuple[RepoContext, List[Change]]:
        # Lightweight checks that don’t run the game:
        # - python -m py_compile on edited files (after edits are applied)
        # We run later; here just record intent.
        ctx.notes.append("[smoke_test] will run py_compile after apply")
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