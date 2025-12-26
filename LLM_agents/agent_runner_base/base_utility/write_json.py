import json, time
from pathlib import Path

def write_json_atomic(path: Path, obj: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(path)  # atomic on same filesystem

def emit_message(bus_dir: Path, msg: dict) -> Path:
    epoch_ms = int(time.time() * 1000)
    trace_id = msg.get("trace_id", "no-trace")
    frm = msg.get("from", "unknown")
    typ = msg.get("type", "unknown")
    out = bus_dir / "outbox" / f"{epoch_ms}__{trace_id}__{frm}__{typ}.json"
    write_json_atomic(out, msg)
    return out