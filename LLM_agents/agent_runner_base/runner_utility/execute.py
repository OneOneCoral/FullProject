from dataclasses import dataclass
from typing import Optional
import subprocess, sys

@dataclass
class AgentRunResult:
    returncode: int
    stdout: str
    stderr: str

def run_agent_module(module: str, cwd: str) -> AgentRunResult:
    cmd = [sys.executable, "-u", "-m", module]
    proc = subprocess.run(cmd, cwd=cwd, text=True, capture_output=True)
    return AgentRunResult(proc.returncode, proc.stdout, proc.stderr)