import json
import re
from typing import TypeVar, Type, Optional
from openai import AsyncOpenAI
from pydantic import BaseModel, ValidationError
from backend import config

T = TypeVar("T", bound=BaseModel)

def get_client() -> AsyncOpenAI:
    # Use dummy key for local servers (Ollama/LM Studio) if not configured
    key = config.LLM_API_KEY.strip() if config.LLM_API_KEY else "not-needed"
    return AsyncOpenAI(
        base_url=config.LLM_BASE_URL.rstrip("/"),
        api_key=key,
        timeout=60.0,
    )

def extract_json_str(text: str) -> str:
    """Extract raw JSON substring from text even if enclosed in markdown code fences."""
    text = text.strip()
    if text.startswith("```"):
        match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text)
        if match:
            return match.group(1).strip()
    # Match outermost curly braces or brackets
    first_brace = text.find("{")
    last_brace = text.rfind("}")
    if first_brace != -1 and last_brace != -1 and last_brace > first_brace:
        return text[first_brace : last_brace + 1]
    return text

async def complete_structured(
    model: str,
    system_prompt: str,
    user_prompt: str,
    schema: Type[T],
    temperature: float = 0.2,
) -> T:
    """
    Calls an OpenAI-compatible endpoint expecting JSON adhering to `schema`.
    Performs exactly one retry on malformed JSON or validation failure.
    """
    if not model:
        raise ValueError("Model ID is not configured.")

    client = get_client()
    json_schema_str = json.dumps(schema.model_json_schema(), indent=2)
    augmented_system = (
        f"{system_prompt}\n\n"
        f"CRITICAL: You must respond ONLY with a single valid JSON object satisfying this JSON Schema:\n"
        f"{json_schema_str}\n"
        f"Do not include any prose, explanations, or text outside the JSON object."
    )

    messages = [
        {"role": "system", "content": augmented_system},
        {"role": "user", "content": user_prompt},
    ]

    last_error: Optional[Exception] = None

    for attempt in range(2):
        try:
            # We request json_object response_format; if endpoint rejects it, fallback to default
            try:
                response = await client.chat.completions.create(
                    model=model,
                    messages=messages,
                    temperature=temperature,
                    response_format={"type": "json_object"},
                )
            except Exception:
                response = await client.chat.completions.create(
                    model=model,
                    messages=messages,
                    temperature=temperature,
                )

            raw_content = response.choices[0].message.content or ""
            cleaned_json = extract_json_str(raw_content)
            parsed_data = schema.model_validate_json(cleaned_json)
            return parsed_data
        except (ValidationError, json.JSONDecodeError, Exception) as err:
            last_error = err
            if attempt == 0:
                messages.append({"role": "assistant", "content": raw_content if "raw_content" in locals() else ""})
                messages.append({
                    "role": "user",
                    "content": f"The response was invalid JSON or did not match the schema: {err}. Output strictly valid JSON only.",
                })
            else:
                break

    raise ValueError(f"Failed to produce valid {schema.__name__} after 1 retry. Error: {last_error}")
