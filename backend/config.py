import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env file from project root
env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

LLM_BASE_URL = os.getenv("LLM_BASE_URL", "https://integrate.api.nvidia.com/v1")
LLM_API_KEY = os.getenv("LLM_API_KEY", "")

DRAFTER_MODEL = os.getenv("DRAFTER_MODEL", "")
JUDGE_MODEL = os.getenv("JUDGE_MODEL", "")
VISION_MODEL = os.getenv("VISION_MODEL", "")
SCANNER_MODEL = os.getenv("SCANNER_MODEL", "")

DRAFTER_WHY = os.getenv("DRAFTER_WHY", "Strong reasoning model that writes actionable, newcomer-friendly issues and applies critiques.")
JUDGE_WHY = os.getenv("JUDGE_WHY", "Independent evaluation model from a distinct family, providing strict and unbiased quality critiques.")
VISION_WHY = os.getenv("VISION_WHY", "Multimodal perception model that inspects UI screenshots and converts them into structured tickets.")
SCANNER_WHY = os.getenv("SCANNER_WHY", "Fast token-efficient scanner to quickly prioritize contribution opportunities.")

DRAFTER_LICENSE = os.getenv("DRAFTER_LICENSE", "Open-weight")
JUDGE_LICENSE = os.getenv("JUDGE_LICENSE", "Open-weight")
VISION_LICENSE = os.getenv("VISION_LICENSE", "Open-weight")
SCANNER_LICENSE = os.getenv("SCANNER_LICENSE", "Open-weight")

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")
TARGET_REPO = os.getenv("TARGET_REPO", "")
DEMO_MODE = os.getenv("DEMO_MODE", "live").lower()

def roles() -> list[dict]:
    """Returns active configured crew roles with models, descriptions, and licenses."""
    all_roles = [
        {"role": "scanner", "model": SCANNER_MODEL, "why": SCANNER_WHY, "license": SCANNER_LICENSE},
        {"role": "drafter", "model": DRAFTER_MODEL, "why": DRAFTER_WHY, "license": DRAFTER_LICENSE},
        {"role": "judge", "model": JUDGE_MODEL, "why": JUDGE_WHY, "license": JUDGE_LICENSE},
        {"role": "vision", "model": VISION_MODEL, "why": VISION_WHY, "license": VISION_LICENSE},
    ]
    return [r for r in all_roles if r["model"]]
