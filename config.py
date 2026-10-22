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

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")
TARGET_REPO = os.getenv("TARGET_REPO", "")
DEMO_MODE = os.getenv("DEMO_MODE", "live").lower()

# One-line explanation for judges on why each model/role exists in the pipeline
ROLE_WHY = {
    "drafter": "Strong reasoning and code understanding to draft actionable, well-scoped contributor issues.",
    "judge": "Independent evaluation model providing unbiased critique, scoring, and gap detection.",
    "vision": "Multimodal perception to inspect UI bug screenshots and convert them into structured tickets.",
    "scanner": "Fast token-efficient scanning to identify TODOs, doc gaps, and contribution candidates.",
}

ROLE_LICENSES = {
    "drafter": "Open-weight",
    "judge": "Open-weight",
    "vision": "Open-weight",
    "scanner": "Open-weight",
}
