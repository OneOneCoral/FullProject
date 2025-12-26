from __future__ import annotations

import json
import time
from dataclasses import asdict, is_dataclass
from pathlib import Path
from typing import Any, Optional


# agent_runner_base/state/store.py  -> repo root for this package is agent_runner_base/
REPO_ROOT = Path(__file__).resolve().parents[1]  # agent_runner_base/
STATE_DIR = REPO_ROOT / "state"
STATE_DIR.mkdir(parents=True, exist_ok=True)

RUNS_DIR = STATE_DIR / "runs"
RUNS_DIR.mkdir(parents=True, exist_ok=True)

LAST_RUN_PATH = STATE_DIR / "last_run.json"


def _json_default(o: Any) -> Any:
    """Fallback for json serialization."""
    if is_dataclass(o):
        return asdict(o)
    if hasattr(o, "to_dict") and callable(getattr(o, "to_dict")):
        return o.to_dict()
    if hasattr(o, "__dict__"):
        return dict(o.__dict__)
    return str(o)


def write_json_atomic(path: Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(obj, ensure_ascii=False, indent=2, default=_json_default), encoding="utf-8")
    tmp.replace(path)


def tail_text(text: str, *, max_lines: int = 200) -> str:
    lines = (text or "").splitlines()
    if len(lines) <= max_lines:
        return text or ""
    return "\n".join(lines[-max_lines:])


def _make_run_record(*, trace_id: str, agent_module: str | None, agent_returncode: int | None, game_result: Any | None) -> dict:
    # game_result can be your RunResult dataclass from game_capture_runner.py OR a dict
    record: dict[str, Any] = {
        "trace_id": trace_id,
        "created_at": time.time(),
        "agent": {
            "module": agent_module,
            "returncode": agent_returncode,
        },
        "game": None,
    }

    if game_result is not None:
        # Normalize to dict
        if isinstance(game_result, dict):
            g = dict(game_result)
        elif is_dataclass(game_result):
            g = asdict(game_result)
        else:
            g = getattr(game_result, "__dict__", {"value": str(game_result)})

        # Keep tails inside JSON so state stays readable
        stdout = g.get("stdout", "")
        stderr = g.get("stderr", "")
        g["stdout_tail"] = tail_text(stdout, max_lines=200)
        g["stderr_tail"] = tail_text(stderr, max_lines=200)

        # Optionally drop full stdout/stderr from state (keep in log files)
        # Comment these two lines out if you want to keep full text in JSON.
        g.pop("stdout", None)
        g.pop("stderr", None)

        record["game"] = g

    return record


def write_run(
    *,
    trace_id: str,
    agent_module: str | None = None,
    agent_returncode: int | None = None,
    game_result: Any | None = None,
) -> Path:
    """
    Writes a full run record under state/runs/<trace_id>.json
    Also updates state/last_run.json for convenience.
    """
    record = _make_run_record(
        trace_id=trace_id,
        agent_module=agent_module,
        agent_returncode=agent_returncode,
        game_result=game_result,
    )

    run_path = RUNS_DIR / f"{trace_id}.json"
    write_json_atomic(run_path, record)
    write_json_atomic(LAST_RUN_PATH, record)
    return run_path


def read_last_run() -> Optional[dict]:
    if not LAST_RUN_PATH.exists():
        return None
    return json.loads(LAST_RUN_PATH.read_text(encoding="utf-8"))


def read_run(trace_id: str) -> Optional[dict]:
    path = RUNS_DIR / f"{trace_id}.json"
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))
