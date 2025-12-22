# test_env.py (repo root)
import os
from pathlib import Path
from dotenv import load_dotenv

def main() -> None:
    repo_root = Path(__file__).resolve().parent
    env_path = repo_root / ".env"

    if not env_path.exists():
        raise FileNotFoundError(f".env file not found at: {env_path}")

    load_dotenv(env_path)
    print("✅ Loaded .env from:", env_path)

    required = ["OPENAI_API_KEY", "GITHUB_USERNAME", "GITHUB_TOKEN"]
    missing = [v for v in required if not os.getenv(v)]
    if missing:
        raise SystemExit(f"❌ Missing required env vars: {', '.join(missing)}")

    print("OPENAI_API_KEY = [loaded]")
    print("GITHUB_USERNAME =", os.getenv("GITHUB_USERNAME"))
    print("GITHUB_TOKEN =", os.getenv("GITHUB_TOKEN")[:6] + "...")
    print("CODERUNNERX_DRY_RUN =", os.getenv("CODERUNNERX_DRY_RUN", "false"))
    print("CODERUNNERX_MODEL =", os.getenv("CODERUNNERX_MODEL", "default"))

    print("✅ Environment OK")

if __name__ == "__main__":
    main()