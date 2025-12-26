from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import os
import subprocess
import sys
import time


@dataclass
class RunResult:
    returncode: int
    duration_sec: float
    stdout: str
    stderr: str
    timed_out: bool
    cmd: list[str]
    cwd: str
    stdout_log: str
    stderr_log: str


def run_game_capture(
    entrypoint: Path,
    cwd: Path,
    trace_id: str,
    *,
    timeout_sec: int = 30,
    headless: bool = False,
    env_extra: dict[str, str] | None = None,
) -> RunResult:
    """
    Run a python game entrypoint and capture stdout/stderr into:
      logs/run_<trace>.stdout.txt
      logs/run_<trace>.stderr.txt

    Returns a RunResult with in-memory stdout/stderr as well.
    """
    entrypoint = Path(entrypoint).resolve()
    cwd = Path(cwd).resolve()

    logs_dir = cwd / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)

    env = os.environ.copy()
    if env_extra:
        env.update(env_extra)

    # Optional: allow pygame to run without a window (CI / headless)
    if headless:
        env.setdefault("SDL_VIDEODRIVER", "dummy")
        env.setdefault("SDL_AUDIODRIVER", "dummy")

    # Unbuffered so we can capture output promptly
    cmd = [sys.executable, "-u", str(entrypoint)]

    out_file = logs_dir / f"run_{trace_id}.stdout.txt"
    err_file = logs_dir / f"run_{trace_id}.stderr.txt"

    start = time.time()
    timed_out = False

    proc = subprocess.Popen(
        cmd,
        cwd=str(cwd),
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    try:
        stdout, stderr = proc.communicate(timeout=timeout_sec)
    except subprocess.TimeoutExpired:
        timed_out = True
        proc.kill()
        stdout, stderr = proc.communicate()

    duration = time.time() - start
    returncode = proc.returncode if proc.returncode is not None else -1

    # Persist logs
    out_file.write_text(stdout or "", encoding="utf-8")
    err_file.write_text(stderr or "", encoding="utf-8")

    return RunResult(
        returncode=returncode,
        duration_sec=duration,
        stdout=stdout or "",
        stderr=stderr or "",
        timed_out=timed_out,
        cmd=cmd,
        cwd=str(cwd),
        stdout_log=str(out_file),
        stderr_log=str(err_file),
    )