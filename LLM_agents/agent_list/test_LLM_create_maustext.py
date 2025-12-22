from __future__ import annotations

import os
import time
from dataclasses import dataclass
from pathlib import Path
from typing import List

from dotenv import load_dotenv


# Reuse your existing safety + paths
from base import STATE_DIR, safe_write_text, Change, apply_changes
from openai import OpenAI

print(">>> Agent module loaded:", __name__)

# Load .env from repo root (same place your runner loads it)
REPO_ROOT = Path(__file__).resolve().parents[1]  # .../LLM_agents
ENV_FILE = REPO_ROOT / ".env"
if ENV_FILE.exists():
    load_dotenv(ENV_FILE)

MODEL = os.getenv("CODERUNNERX_MODEL", "gpt-4.1")
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

SYSTEM = (
    "You are a helpful assistant that writes short cute storys.\n"
    "Write a short story of a gaming mouse and its adventures.\n"
    "Keep it ~80-140 words.\n"
)
class GamingMouseTextAgent:
    name = "gaming_mouse_agent"

    def generate_text(self) -> str:
        resp = client.responses.create(
            model=MODEL,
            input=[
                {"role": "system", "content": SYSTEM},
                {"role": "user", "content": "Write the gaming mouse text now."},
            ],
        )
        return (resp.output_text or "").strip()

    def run(self) -> List[Change]:
        text = self.generate_text()

        timestamp = time.strftime("%Y%m%d-%H%M%S")
        target = STATE_DIR / f"gaming_mouse_{timestamp}.txt"

        content = (
            "Gaming Mouse Description\n"
            "========================\n\n"
            f"{text}\n"
        )

        return [
            Change(
                path=target,
                summary="Generate a short gaming mouse text with the LLM and save to state/",
                content=content,
            )
        ]

def main() -> None:
    agent = GamingMouseTextAgent()
    changes = agent.run()
    apply_changes(changes)

if __name__ == "__main__":
    main()