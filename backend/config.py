import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env file from project root
env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=env_path, override=True)

LLM_BASE_URL = os.getenv("LLM_BASE_URL", "https://integrate.api.nvidia.com/v1")
LLM_API_KEY = os.getenv("LLM_API_KEY", "")

# Crew models
DRAFTER_MODEL = os.getenv("DRAFTER_MODEL", "")
JUDGE_MODEL = os.getenv("JUDGE_MODEL", "")
REWRITE_MODEL = os.getenv("REWRITE_MODEL", "")
CODE_MODEL = os.getenv("CODE_MODEL", "")
VISION_MODEL = os.getenv("VISION_MODEL", "")
SCANNER_MODEL = os.getenv("SCANNER_MODEL", "")

# Role explanations
DRAFTER_WHY = os.getenv("DRAFTER_WHY", "Deep code context synthesis & structured JSON drafting")
JUDGE_WHY = os.getenv("JUDGE_WHY", "Independent reasoning critique to catch hallucinations")
REWRITE_WHY = os.getenv("REWRITE_WHY", "Dedicated Gemma model to polish acceptance criteria and enforce testability")
CODE_WHY = os.getenv("CODE_WHY", "Qwen-powered static source analysis and line-level bug evidence extraction")
VISION_WHY = os.getenv("VISION_WHY", "Multimodal perception model that inspects UI screenshots and converts them into structured tickets.")
SCANNER_WHY = os.getenv("SCANNER_WHY", "Fast token-efficient scanner to quickly prioritize contribution opportunities.")

# Licenses
DRAFTER_LICENSE = os.getenv("DRAFTER_LICENSE", "Open-weight")
JUDGE_LICENSE = os.getenv("JUDGE_LICENSE", "Open-weight")
REWRITE_LICENSE = os.getenv("REWRITE_LICENSE", "Open-weight")
CODE_LICENSE = os.getenv("CODE_LICENSE", "Open-weight")
VISION_LICENSE = os.getenv("VISION_LICENSE", "Open-weight")
SCANNER_LICENSE = os.getenv("SCANNER_LICENSE", "Open-weight")

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")
TARGET_REPO = os.getenv("TARGET_REPO", "")
DEMO_MODE = os.getenv("DEMO_MODE", "live").lower()

def reload():
    """Reloads environment variables from .env to ensure runtime updates take effect without server restart."""
    load_dotenv(dotenv_path=env_path, override=True)
    global LLM_BASE_URL, LLM_API_KEY
    global DRAFTER_MODEL, JUDGE_MODEL, REWRITE_MODEL, CODE_MODEL, VISION_MODEL, SCANNER_MODEL
    global DRAFTER_WHY, JUDGE_WHY, REWRITE_WHY, CODE_WHY, VISION_WHY, SCANNER_WHY
    global DRAFTER_LICENSE, JUDGE_LICENSE, REWRITE_LICENSE, CODE_LICENSE, VISION_LICENSE, SCANNER_LICENSE
    global GITHUB_TOKEN, TARGET_REPO, DEMO_MODE

    LLM_BASE_URL = os.getenv("LLM_BASE_URL", "https://integrate.api.nvidia.com/v1")
    LLM_API_KEY = os.getenv("LLM_API_KEY", "")

    DRAFTER_MODEL = os.getenv("DRAFTER_MODEL", "")
    JUDGE_MODEL = os.getenv("JUDGE_MODEL", "")
    REWRITE_MODEL = os.getenv("REWRITE_MODEL", "")
    CODE_MODEL = os.getenv("CODE_MODEL", "")
    VISION_MODEL = os.getenv("VISION_MODEL", "")
    SCANNER_MODEL = os.getenv("SCANNER_MODEL", "")

    DRAFTER_WHY = os.getenv("DRAFTER_WHY", "Deep code context synthesis & structured JSON drafting")
    JUDGE_WHY = os.getenv("JUDGE_WHY", "Independent reasoning critique to catch hallucinations")
    REWRITE_WHY = os.getenv("REWRITE_WHY", "Dedicated Gemma model to polish acceptance criteria and enforce testability")
    CODE_WHY = os.getenv("CODE_WHY", "Qwen-powered static source analysis and line-level bug evidence extraction")
    VISION_WHY = os.getenv("VISION_WHY", "Multimodal perception model that inspects UI screenshots and converts them into structured tickets.")
    SCANNER_WHY = os.getenv("SCANNER_WHY", "Fast token-efficient scanner to quickly prioritize contribution opportunities.")

    DRAFTER_LICENSE = os.getenv("DRAFTER_LICENSE", "Open-weight")
    JUDGE_LICENSE = os.getenv("JUDGE_LICENSE", "Open-weight")
    REWRITE_LICENSE = os.getenv("REWRITE_LICENSE", "Open-weight")
    CODE_LICENSE = os.getenv("CODE_LICENSE", "Open-weight")
    VISION_LICENSE = os.getenv("VISION_LICENSE", "Open-weight")
    SCANNER_LICENSE = os.getenv("SCANNER_LICENSE", "Open-weight")

    GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")
    TARGET_REPO = os.getenv("TARGET_REPO", "")
    DEMO_MODE = os.getenv("DEMO_MODE", "live").lower()

def roles() -> list[dict]:
    """Returns active configured crew roles with models, descriptions, and licenses."""
    reload()
    all_roles = [
        {"role": "scanner", "model": SCANNER_MODEL, "why": SCANNER_WHY, "license": SCANNER_LICENSE},
        {"role": "code_analysis", "model": CODE_MODEL, "why": CODE_WHY, "license": CODE_LICENSE},
        {"role": "drafter", "model": DRAFTER_MODEL, "why": DRAFTER_WHY, "license": DRAFTER_LICENSE},
        {"role": "judge", "model": JUDGE_MODEL, "why": JUDGE_WHY, "license": JUDGE_LICENSE},
        {"role": "rewrite", "model": REWRITE_MODEL or DRAFTER_MODEL, "why": REWRITE_WHY, "license": REWRITE_LICENSE},
        {"role": "vision", "model": VISION_MODEL, "why": VISION_WHY, "license": VISION_LICENSE},
    ]
    return [r for r in all_roles if r["model"]]
