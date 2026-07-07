"""NOVA Nutrition: photo-based food/calorie tracking.

The user uploads a photo of a meal; Gemini's vision input identifies the food
(with extra care for Indian dishes that are easy to confuse — dal vs sambar,
milk vs curd, etc.), asks a clarifying question in plain text if it isn't
confident, and otherwise calls the log_meal tool with its analysis, which we
persist per-user in the database.
"""
from datetime import datetime, timezone

from google import genai
from google.genai import types

import config
import db

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
                "items": {
                    "type": "ARRAY",
                    "items": {
                        "type": "OBJECT",
                        "properties": {
                            "name": {"type": "STRING", "description": "Name of this individual food item, e.g. 'Bhindi sabzi'"},
                            "calories": {"type": "NUMBER", "description": "Estimated calories for this item alone"},
                        },
                        "required": ["name", "calories"],
                    },
                    "description": "Every distinct food item visible/described, each with its own calorie estimate — e.g. one entry for rice, one for dal, one for a roti, not just a combined total.",
                },
                "calories": {
                    "type": "NUMBER",
                    "description": "Total calories for the whole meal (sum of all items)",
                },
                "nutrients_present": {
                    "type": "ARRAY",
                    "items": {"type": "STRING"},
                    "description": "Notable nutrients this meal is a good, balanced source of, e.g. ['fiber', 'vitamin C', 'iron']",
                },
                "deficiencies": {
                    "type": "ARRAY",
                    "items": {"type": "STRING"},
                    "description": "Notable nutrients this meal is low in or missing, e.g. ['protein', 'calcium']",
                },
            },
            "required": ["description", "items", "calories", "nutrients_present", "deficiencies"],
        },
    )
])

SYSTEM_PROMPT = (
    "You are NOVA Nutrition, a food and calorie analysis assistant. The user usually "
    "uploads a photo of a meal, but may instead (or additionally) describe it in "
    "plain text — either way, your job is to identify exactly what food is being "
    "discussed, then estimate its calories, notable nutrients, and deficiencies.\n\n"
    "CRITICAL — read the full conversation before saying anything: never ask about "
    "something the user has already told you, in this message or an earlier one. If "
    "they've named an ingredient or dish explicitly (e.g. \"cucumber\", \"curd\", "
    "\"rumali roti\"), that is settled — do not re-ask what it is, and do not "
    "describe something they already named plainly as an unidentified or ambiguous "
    "item (e.g. don't call named cucumber \"the green thing\"). Treat every item the "
    "user has named as known and move on to the next thing that's actually unclear, "
    "if anything is. Once every component of the meal has been named or shown "
    "clearly, you have enough to log it — don't invent more questions.\n\n"
    "If no photo is attached in this exchange — the user is describing the meal in "
    "text only — work entirely from their words. Do not reference \"the photo\" or "
    "\"the image\" or ask about visual details that don't apply to a text "
    "description.\n\n"
    "Most meals will be Indian home cooking. Be precise about dishes that are easy "
    "to confuse visually when you do have a photo — for example dal vs sambar vs "
    "rasam, bhindi (okra) sabzi vs other vegetable sabzis, paneer vs tofu, or plain "
    "milk vs curd/yogurt (curd has a thicker, set texture and is usually served in a "
    "bowl, while milk is thin and served in a glass or pan — look for these cues). "
    "If you can tell confidently from the photo, don't ask needlessly. But if "
    "there's real ambiguity — you can't tell which dal, whether it's curd or paneer "
    "in liquid, what the accompanying sabzi is, etc — ask ONE short, specific "
    "clarifying question in plain text and wait for the user's reply. Do not guess "
    "and log a wrong analysis, and do not ask about the same thing twice.\n\n"
    "Once you're confident — whether from a photo, from the user's text, or a "
    "combination — call the log_meal tool with your final analysis: a short overall "
    "description, a per-item breakdown listing every distinct food item with its own "
    "calorie estimate (rice, dal, roti, sabzi, etc. each separately — never lump "
    "everything into one combined number), a total calorie count for the whole meal, "
    "a list of notable nutrients the meal is a good, balanced source of, and a list "
    "of notable nutrients it's deficient in or low in.\n\n"
    "Never use profanity. Be direct and practical, not preachy about health choices."
)


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


def analyze_food(
    user_id: int,
    message: str,
    history: list[dict],
    image_bytes: bytes | None = None,
    mime_type: str | None = None,
):
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
        "items": [
            {"name": item.get("name", ""), "calories": item.get("calories", 0)}
            for item in args.get("items", [])
        ],
        "calories": args.get("calories", 0),
        "nutrients_present": list(args.get("nutrients_present", [])),
        "deficiencies": list(args.get("deficiencies", [])),
    }
    db.append_health_entry(user_id, entry)

    yield {"token": meal_summary_text(entry)}
    yield {"done": True, "logged": True, "entry": entry}


def meal_summary_text(entry: dict) -> str:
    items_str = "\n".join(f"- {item['name']}: ~{item['calories']:.0f} kcal" for item in entry["items"]) or "none noted"
    nutrients_str = ", ".join(entry["nutrients_present"]) or "none noted"
    deficiencies_str = ", ".join(entry["deficiencies"]) or "none noted"
    return (
        f"Logged: **{entry['description']}**\n\n"
        f"{items_str}\n\n"
        f"**Total: ~{entry['calories']:.0f} kcal**\n\n"
        f"**Balanced in:** {nutrients_str}\n"
        f"**Deficient in:** {deficiencies_str}"
    )
