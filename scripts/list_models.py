import asyncio
import time
import sys
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

from backend import config
from backend.llm import get_client

async def test_model(client, model_id: str, role_name: str):
    print(f"\nTesting {role_name.upper()} model ({model_id})...", end=" ", flush=True)
    t0 = time.time()
    try:
        response = await client.chat.completions.create(
            model=model_id,
            messages=[{"role": "user", "content": "Respond with the word OK."}],
            max_tokens=150,
            temperature=0.0,
        )
        elapsed = round((time.time() - t0) * 1000)
        msg = response.choices[0].message if response.choices else None
        raw_text = getattr(msg, "content", None) or getattr(msg, "reasoning_content", None) or ""
        content = (raw_text or "").strip()
        print(f"[PASS] ({elapsed}ms) -> response: {repr(content[:30])}")
        return True
    except Exception as e:
        elapsed = round((time.time() - t0) * 1000)
        print(f"[FAIL] ({elapsed}ms) -> {e}")
        return False

async def main():
    print("=" * 60)
    print("Kindling - Model Discovery & Sanity Checker")
    print(f"Target Base URL: {config.LLM_BASE_URL}")
    print(f"API Key present: {'Yes (Length: ' + str(len(config.LLM_API_KEY)) + ')' if config.LLM_API_KEY else 'No'}")
    print("=" * 60)

    client = get_client()

    print("\nQuerying available models via GET /models...")
    available_models = []
    try:
        models_page = await client.models.list()
        # Sort model IDs
        available_models = sorted([m.id for m in models_page.data])
        print(f"Discovered {len(available_models)} model(s).")
        
        # Display sample or popular models
        filter_terms = ["llama", "nemotron", "gemma", "mistral", "mixtral", "qwen"]
        relevant = [m for m in available_models if any(term in m.lower() for term in filter_terms)]
        
        if relevant:
            print("\nPopular / Open-Weight Models Available:")
            for m in relevant[:30]:
                print(f"  - {m}")
            if len(relevant) > 30:
                print(f"  ... and {len(relevant) - 30} more matching models.")
        else:
            print("First 20 available models:")
            for m in available_models[:20]:
                print(f"  - {m}")
    except Exception as e:
        print(f"Failed to fetch model list: {e}")
        print("Note: Some providers restrict /models listing or require specific auth headers.")

    print("\n" + "=" * 60)
    print("Testing Configured Roles from .env:")
    configured_roles = {
        "drafter": config.DRAFTER_MODEL,
        "judge": config.JUDGE_MODEL,
        "vision": config.VISION_MODEL,
        "scanner": config.SCANNER_MODEL,
    }

    results = {}
    for role, model_id in configured_roles.items():
        if not model_id:
            print(f"\n{role.upper()}: [NOT CONFIGURED] (Set {role.upper()}_MODEL in .env)")
            results[role] = None
        else:
            ok = await test_model(client, model_id, role)
            results[role] = ok

    print("\n" + "=" * 60)
    print("Summary:")
    for role, status in results.items():
        status_str = "READY" if status is True else ("FAILED" if status is False else "OPTIONAL / SKIPPED")
        print(f"  {role:8s} -> {configured_roles[role] or '(empty)'} [{status_str}]")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(main())
