import json
import re
import time
from typing import TypeVar, Type, Optional, Tuple
from openai import AsyncOpenAI
from pydantic import BaseModel, ValidationError
from backend import config
import logging

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)

_client: Optional[AsyncOpenAI] = None


def get_client() -> AsyncOpenAI:
    """Returns cached AsyncOpenAI client configured from environment variables."""
    global _client
    if _client is None:
        key = config.LLM_API_KEY.strip() if config.LLM_API_KEY else "not-needed"
        _client = AsyncOpenAI(
            base_url=config.LLM_BASE_URL.rstrip("/"),
            api_key=key,
            timeout=90.0,
        )
    return _client


def extract_json(text: str) -> dict:
    """Strips code fences and extracts the outermost JSON object as a dict."""
    text = text.strip()
    if text.startswith("```"):
        match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text)
        if match:
            text = match.group(1).strip()
    first_brace = text.find("{")
    last_brace = text.rfind("}")
    if first_brace != -1 and last_brace != -1 and last_brace > first_brace:
        json_candidate = text[first_brace : last_brace + 1]
        return json.loads(json_candidate)
    return json.loads(text)


def _strip_thinking_tags(text: str) -> str:
    """Removes <think>...</think> blocks emitted by deep thinking/reasoning models."""
    cleaned = re.sub(r"<think>[\s\S]*?</think>", "", text)
    return cleaned.strip()


def _get_model_for_role(role: str) -> str:
    role_lower = role.lower()
    if role_lower == "drafter":
        return config.DRAFTER_MODEL
    elif role_lower == "judge":
        return config.JUDGE_MODEL
    elif role_lower == "rewrite":
        return config.REWRITE_MODEL or config.DRAFTER_MODEL
    elif role_lower in ("code", "code_analysis"):
        return config.CODE_MODEL
    elif role_lower == "vision":
        return config.VISION_MODEL
    elif role_lower == "scanner":
        return config.SCANNER_MODEL
    raise ValueError(f"Unknown role '{role}'. Expected drafter, judge, rewrite, code_analysis, vision, or scanner.")

async def chat(
    role: str,
    messages: list[dict],
    max_tokens: int = 2500,
    temperature: float = 0.3,
) -> Tuple[str, int]:
    """
    Executes a chat completion for the assigned role.
    Returns (cleaned_text, duration_ms).
    """
    model = _get_model_for_role(role)
    if not model:
        raise ValueError(f"No model configured for role '{role}'. Check your .env file.")

    client = get_client()
    t0 = time.time()

    # Attempt json_object format first; gracefully fallback if endpoint doesn't support it
    '''try:
        response = await client.chat.completions.create(
            model=model,
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature,
            response_format={"type": "json_object"},
        )
    except Exception:
        response = await client.chat.completions.create(
            model=model,
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature,
        )'''

    try:
        response = await client.chat.completions.create(
            model=model,
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature,
            response_format={"type": "json_object"},
        )
    except Exception as first_error:
        logger.warning(
            "NVIDIA request with json_object failed: %s",
            first_error,
            stack_info=True,
        )

        response = await client.chat.completions.create(
            model=model,
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature,
        )

    duration_ms = round((time.time() - t0) * 1000)
    choice = response.choices[0]
    msg = choice.message
    raw_content = getattr(msg, "content", None)
    if not raw_content:
        raw_content = getattr(msg, "reasoning_content", None) or ""

    cleaned_text = _strip_thinking_tags(raw_content)
    return cleaned_text, duration_ms


async def chat_json(
    role: str,
    system: str,
    user: str,
    schema: Type[T],
    max_tokens: int = 2500,
) -> Tuple[T, int]:
    """
    Calls chat() expecting a JSON response matching `schema`.
    Performs exactly one retry on malformed JSON or validation failure.
    Returns (validated_model, total_duration_ms).
    """
    json_schema_str = json.dumps(schema.model_json_schema(), indent=2)
    augmented_system = (
        f"{system}\n\n"
        f"CRITICAL: Output MUST be a single valid JSON object adhering strictly to this schema:\n"
        f"{json_schema_str}\n"
        f"Do not include any Markdown text outside the JSON object."
    )

    messages = [
        {"role": "system", "content": augmented_system},
        {"role": "user", "content": user},
    ]

    total_duration_ms = 0
    last_error: Optional[Exception] = None

    for attempt in range(2):
        text, duration_ms = await chat(role, messages, max_tokens=max_tokens)
        total_duration_ms += duration_ms

        try:
            parsed_dict = extract_json(text)
            validated_obj = schema.model_validate(parsed_dict)
            return validated_obj, total_duration_ms
        except Exception as err:
            last_error = err
            if attempt == 0:
                messages.append({"role": "assistant", "content": text})
                messages.append({
                    "role": "user",
                    "content": "Your last reply was not valid JSON for the schema. Return ONLY the JSON object, no prose.",
                })

    raise ValueError(f"Model for role '{role}' failed to return valid {schema.__name__} after 1 retry: {last_error}")

# Backward compatibility alias
complete_structured = chat_json

# Error Logging Function

logger = logging.getLogger(__name__)

