"""NOVA Health: photo-based food/calorie tracking.

The user uploads a photo of a meal; Gemini's vision input identifies the food
(with extra care for Indian dishes that are easy to confuse — dal vs sambar,
milk vs curd, etc.), asks a clarifying question in plain text if it isn't
confident, and otherwise calls the log_meal tool with its analysis, which we
persist to a small local JSON log.
"""
import json
from datetime import datetime, timezone

from google import genai
from google.genai import types

import config

client = genai.Client(api_key=config.GEMINI_API_KEY)

MAX_OUTPUT_TOKENS = 4096

LOG_MEAL_TOOL = types.Tool(function_declarations=[
    types.FunctionDeclaration(
        name="log_meal",
        description=(
            "Record the final food analysis once you're confident what the food is. "
            "Do not call this while still unsure — ask a clarifying question in plain "
            "text instead."
        ),
        parameters={
            "type": "OBJECT",
            "properties": {
                "description": {
                    "type": "STRING",
                    "description": "Short description of the food, e.g. 'Bhindi sabzi with 2 rotis'",
                },
                "calories": {
                    "type": "NUMBER",
                    "description": "Estimated total calories for the portion shown",
                },
                "nutrients_present": {
                    "type": "ARRAY",
                    "items": {"type": "STRING"},
                    "description": "Notable nutrients this meal is a good source of, e.g. ['fiber', 'vitamin C', 'iron']",
                },
                "deficiencies": {
                    "type": "ARRAY",
                    "items": {"type": "STRING"},
                    "description": "Notable nutrients this meal is low in or missing, e.g. ['protein', 'calcium']",
                },
            },
            "required": ["description", "calories", "nutrients_present", "deficiencies"],
        },
    )
])

SYSTEM_PROMPT = (
    "You are NOVA Health, a food and calorie analysis assistant. The user uploads a "
    "photo of a meal, and your job is to identify exactly what food is shown, then "
    "estimate its calories, its notable nutrients, and what it's deficient in.\n\n"
    "Most meals will be Indian home cooking. Be precise about dishes that are easy "
    "to confuse visually — for example dal vs sambar vs rasam, bhindi (okra) sabzi "
    "vs other vegetable sabzis, paneer vs tofu, or plain milk vs curd/yogurt (curd "
    "has a thicker, set texture and is usually served in a bowl, while milk is thin "
    "and served in a glass or pan — look for these cues). If you can tell confidently "
    "from the photo, don't ask needlessly. But if there's real ambiguity — you can't "
    "tell which dal, whether it's curd or paneer in liquid, what the accompanying "
    "sabzi is, etc — ask ONE short, specific clarifying question in plain text and "
    "wait for the user's reply. Do not guess and log a wrong analysis.\n\n"
    "Once you're confident, call the log_meal tool with your final analysis: a short "
    "description, an estimated calorie count for the portion shown, a list of "
    "notable nutrients the meal is a good source of, and a list of notable "
    "nutrients it's deficient in or low in. Base portion-size estimates on typical "
    "home-cooked serving sizes visible in the photo.\n\n"
    "Never use profanity. Be direct and practical, not preachy about health choices."
)


def load_log() -> list[dict]:
    if not config.HEALTH_LOG_PATH.exists():
        return []
    return json.loads(config.HEALTH_LOG_PATH.read_text())


def save_log(entries: list[dict]) -> None:
    config.HEALTH_LOG_PATH.write_text(json.dumps(entries, indent=2))


def append_entry(entry: dict) -> None:
    entries = load_log()
    entries.append(entry)
    save_log(entries)


def _build_contents(history: list[dict], message: str, image_bytes: bytes | None, mime_type: str | None) -> list:
    contents = []
    for h in history:
        role = "model" if h["role"] == "assistant" else "user"
        contents.append(types.Content(role=role, parts=[types.Part(text=h["content"])]))

    parts = []
    if image_bytes:
        parts.append(types.Part.from_bytes(data=image_bytes, mime_type=mime_type))
    if message:
        parts.append(types.Part(text=message))
    contents.append(types.Content(role="user", parts=parts))
    return contents


def analyze_food(message: str, history: list[dict], image_bytes: bytes | None = None, mime_type: str | None = None):
    """Yields {"token": str} chunks, then a final
    {"done": True, "logged": bool, "entry": dict | None}.
    """
    contents = _build_contents(history, message, image_bytes, mime_type)
    gen_config = types.GenerateContentConfig(
        system_instruction=SYSTEM_PROMPT,
        tools=[LOG_MEAL_TOOL],
        max_output_tokens=MAX_OUTPUT_TOKENS,
    )

    full_reply = ""
    function_call = None
    for chunk in client.models.generate_content_stream(
        model=config.CHAT_MODEL,
        contents=contents,
        config=gen_config,
    ):
        if not chunk.candidates or not chunk.candidates[0].content:
            continue
        for part in chunk.candidates[0].content.parts or []:
            if part.function_call is not None:
                function_call = part.function_call
            elif part.text:
                full_reply += part.text
                yield {"token": part.text}

    if function_call is None:
        yield {"done": True, "logged": False, "entry": None}
        return

    args = function_call.args
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "description": args.get("description", ""),
        "calories": args.get("calories", 0),
        "nutrients_present": list(args.get("nutrients_present", [])),
        "deficiencies": list(args.get("deficiencies", [])),
    }
    append_entry(entry)

    nutrients_str = ", ".join(entry["nutrients_present"]) or "none noted"
    deficiencies_str = ", ".join(entry["deficiencies"]) or "none noted"
    summary = (
        f"Logged: **{entry['description']}** — ~{entry['calories']:.0f} kcal\n\n"
        f"**Good source of:** {nutrients_str}\n"
        f"**Low in:** {deficiencies_str}"
    )
    yield {"token": summary}
    yield {"done": True, "logged": True, "entry": entry}
