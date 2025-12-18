import hmac, hashlib, os, subprocess
from flask import Flask, request, abort

app = Flask(__name__)

WEBHOOK_SECRET = os.environ.get("WEBHOOK_SECRET", "CHANGE_ME")
REPO_PATH = os.environ.get("REPO_PATH", r"C:\Users\carlw\pygame")
BRANCH = os.environ.get("BRANCH", "Version1")

FORCE_SYNC = False  # set True if you never edit locally and want hard reset

def verify_signature(raw: bytes, sig_header: str | None) -> bool:
    if not sig_header:
        return False
    try:
        algo, their_sig = sig_header.split("=", 1)
    except ValueError:
        return False
    if algo != "sha256":
        return False
    mac = hmac.new(WEBHOOK_SECRET.encode("utf-8"), msg=raw, digestmod=hashlib.sha256)
    return hmac.compare_digest(mac.hexdigest(), their_sig)

def run_cmd(cmd):
    p = subprocess.run(cmd, cwd=REPO_PATH, capture_output=True, text=True)
    out = (p.stdout or "") + (p.stderr or "")
    return p.returncode, out.strip()

@app.route("/webhook", methods=["POST"])
def webhook():
    raw = request.get_data()
    if not verify_signature(raw, request.headers.get("X-Hub-Signature-256")):
        abort(401, "Bad signature")

    event = request.headers.get("X-GitHub-Event", "")
    if event == "ping":
        return ("pong", 200)
    if event != "push":
        return ("ignored", 200)

    payload = request.json or {}
    ref = payload.get("ref", "")
    if ref != f"refs/heads/{BRANCH}":
        return (f"ignored branch {ref}", 200)

    code, out = run_cmd(["git", "fetch", "origin"])
    if code != 0:
        return ("fetch failed\n" + out, 500)

    if FORCE_SYNC:
        code, out2 = run_cmd(["git", "reset", "--hard", f"origin/{BRANCH}"])
    else:
        code, out2 = run_cmd(["git", "pull", "origin", BRANCH])

    if code == 0:
        return ("updated\n" + out + "\n" + out2, 200)
    return ("update failed\n" + out + "\n" + out2, 500)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)