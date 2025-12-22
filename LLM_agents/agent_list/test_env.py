# test_env_load.py
import os
from pathlib import Path
from dotenv import load_dotenv

def main() -> None:
    """
    Loads .env from the same directory as this file
    and validates required environment variables.
    """

    env_path = Path(__file__).parent / ".env"

    if not env_path.exists():
        raise FileNotFoundError(f".env file not found at: {env_path}")

    load_dotenv(env_path)
    print("✅ Loaded .env from:", env_path)

    # Required variables
    required_vars = [
        "OPENAI_API_KEY",
        "GITHUB_USERNAME",
        "GITHUB_TOKEN",
    ]

    missing = [v for v in required_vars if not os.getenv(v)]
    if missing:
        raise SystemExit(f"❌ Missing required env vars: {', '.join(missing)}")

    # Safe diagnostics (never print secrets)
    print("OPENAI_API_KEY = [loaded]")
    print("GITHUB_USERNAME =", os.getenv("GITHUB_USERNAME"))
    print(
        "GITHUB_TOKEN =",
        os.getenv("GITHUB_TOKEN")[:6] + "..." if os.getenv("GITHUB_TOKEN") else "None"
    )
    print("CODERUNNERX_DRY_RUN =", os.getenv("CODERUNNERX_DRY_RUN", "false"))
    print("CODERUNNERX_MODEL =", os.getenv("CODERUNNERX_MODEL", "default"))

    print("✅ Environment looks good.")

if __name__ == "__main__":
    main()