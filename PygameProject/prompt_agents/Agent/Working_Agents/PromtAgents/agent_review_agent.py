from __future__ import annotations

import json
from time import time
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI

from pygame.Agent.Working_Agents.base import AgentReport, new_run_id, write_report, REPO_ROOT, list_reports

ENV_PATH = REPO_ROOT / "Agent" / ".env"
load_dotenv(ENV_PATH)
client = OpenAI()

SYSTEM = """You are an agent system reviewer.

You will be given recent agent reports and the agent folder file list.
Your job:
- Suggest improvements to agent prompts, safety, discovery, batching, and logging.
- Each suggestion must be actionable and reference a specific file + change intent.

Return strict JSON ONLY:
{
  "suggestions": [
    {
      "id": 1,
      "title": "Short title",
      "reason": "Why this helps",
      "target_files": ["<abs path>", ...],
      "instructions": "Exact instructions for what to change (no code required)"
    }
  ]
}
"""

def run() -> Path:
    run_id = new_run_id("agent_review")

    reports = list_reports()[-12:]  # last N reports
    report_payload = []
    for p in reports:
        try:
            report_payload.append(json.loads(p.read_text(encoding="utf-8")))
        except Exception:
            continue

    agent_files = sorted([str(p) for p in (REPO_ROOT / "Agent").rglob("*.py")])

    payload = {
        "repo_root": str(REPO_ROOT),
        "recent_reports": report_payload,
        "agent_files": agent_files,
    }

    resp = client.responses.create(
        model="gpt-4.1",
        input=[
            {"role": "system", "content": SYSTEM},
            {"role": "user", "content": json.dumps(payload)},
        ],
    )
    data = json.loads(resp.output_text)

    report = AgentReport(
        agent_name="agent_review",
        run_id=run_id,
        created_at=time(),
        ok=True,
        summary=f"Generated {len(data.get('suggestions', []))} improvement suggestions for agents.",
        data=data,
        artifacts=agent_files,
    )
    return write_report(report)

if __name__ == "__main__":
    out = run()
    print("Wrote report:", out)
