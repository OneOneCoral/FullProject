from datetime import datetime, timezone
from pathlib import Path
import os

from .write_json import emit_message

BUS_DIR = Path("agent_runner_base/agent_runtime/bus")

def publish_text(text: str, x: int, y: int) -> None:
    msg = {
        "v": 1,
        "trace_id": os.environ.get("TRACE_ID", "no-trace"),
        "from": "mouse_text_agent",
        "type": "mouse_text",
        "ts": datetime.now(timezone.utc).isoformat(),
        "payload": {"text": text, "x": x, "y": y, "size": 24, "font": "default"},
    }
    emit_message(BUS_DIR, msg)