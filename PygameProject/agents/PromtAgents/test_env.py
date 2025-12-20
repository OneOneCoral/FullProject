# test_env_load.py
import os
from dotenv import load_dotenv
from pathlib import Path

# Load .env file from this directory
env_path = Path(__file__).parent / ".env"
load_dotenv(env_path)

print("✅ Loaded .env from:", env_path)
print("OPENAI_API_KEY =", os.getenv("OPENAI_API_KEY"))
print("GITHUB_USERNAME =", os.getenv("GITHUB_USERNAME"))
print("GITHUB_TOKEN =", os.getenv("GITHUB_TOKEN")[:6] + "..." if os.getenv("GITHUB_TOKEN") else "None")
print("CODERUNNERX_DRY_RUN =", os.getenv("CODERUNNERX_DRY_RUN"))