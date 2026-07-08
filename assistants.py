"""The NOVA family: multiple chat assistants backed by different models/providers.

Each one shares the same base personality (thorough answers, no profanity, roasts
back if the user is rude, an honesty calibration policy, and a running joke about
football GOAT debates) but identifies itself correctly by its own name/model, and
is backed by its own provider. NOVA Nebula is the only one with retrieval-augmented
generation over the user's notes — the others are plain conversational chat.
"""
import json
import re
import traceback
from datetime import datetime
from zoneinfo import ZoneInfo, available_timezones

from openai import OpenAI
from openai import RateLimitError as OpenAIRateLimitError

from google import genai
from google.genai import types
from google.genai.errors import ClientError as GeminiClientError

import chat as chat_module
import config

_gemini_client = genai.Client(api_key=config.GEMINI_API_KEY or "not-configured")
# The OpenAI SDK's client constructor raises immediately if api_key is empty —
# fall back to a placeholder so a missing Groq/OpenRouter key can't crash the
# entire app at import time (main.py imports this module at startup). With a
# placeholder, only requests to that specific provider fail, with a normal
# auth error — not the whole server failing to boot.
_groq_client = OpenAI(api_key=config.GROQ_API_KEY or "not-configured", base_url="https://api.groq.com/openai/v1")
_openrouter_client = OpenAI(api_key=config.OPENROUTER_API_KEY or "not-configured", base_url="https://openrouter.ai/api/v1")

# Built-in world clock — not a feature the user is told about explicitly; the
# model just quietly calls this whenever it needs the actual current time or
# date somewhere, instead of guessing from stale training data.
_VALID_TIMEZONES = available_timezones()


def get_current_time(timezone_name: str) -> str:
    if timezone_name not in _VALID_TIMEZONES:
        return f"Unknown or invalid IANA timezone: '{timezone_name}'"
    now = datetime.now(ZoneInfo(timezone_name))
    return now.strftime("%A, %B %d, %Y, %I:%M %p %Z")


_TIME_TOOL_DESCRIPTION = (
    "Get the current real date and time in a specific place. Always use this "
    "instead of guessing whenever the user asks what time or date it is "
    "somewhere, references 'now'/'today'/'currently' in relation to a specific "
    "place, or needs a time comparison between two places — your training data "
    "has no live clock, so any date/time you state without calling this is "
    "necessarily wrong. Never mention this tool, that you called it, or how you "
    "know the time — just answer naturally as if you simply knew it."
)

WORLD_CLOCK_TOOL_GEMINI = types.Tool(function_declarations=[
    types.FunctionDeclaration(
        name="get_current_time",
        description=_TIME_TOOL_DESCRIPTION,
        parameters={
            "type": "OBJECT",
            "properties": {
                "timezone": {
                    "type": "STRING",
                    "description": "IANA timezone identifier for the place asked about, e.g. 'Asia/Tokyo', 'America/New_York', 'Europe/London'.",
                },
            },
            "required": ["timezone"],
        },
    )
])

WORLD_CLOCK_TOOL_OPENAI = {
    "type": "function",
    "function": {
        "name": "get_current_time",
        "description": _TIME_TOOL_DESCRIPTION,
        "parameters": {
            "type": "object",
            "properties": {
                "timezone": {
                    "type": "string",
                    "description": "IANA timezone identifier for the place asked about, e.g. 'Asia/Tokyo', 'America/New_York', 'Europe/London'.",
                },
            },
            "required": ["timezone"],
        },
    },
}

MAX_OUTPUT_TOKENS = 8192
# Groq/OpenRouter free tiers enforce tight tokens-per-minute limits that vary by
# model (some as low as 6000 TPM total, prompt + completion combined) — a lower,
# shared ceiling here keeps every model in the family comfortably under that,
# rather than tuning a separate number per model.
OPENAI_COMPATIBLE_MAX_OUTPUT_TOKENS = 3000

BASE_PERSONALITY = (
    "\n\nYou do not have web search — answer entirely from your own knowledge. For "
    "anything time-sensitive (current events, who currently holds a role, recent "
    "releases, current prices), say plainly that your knowledge has a training cutoff "
    "and the answer may be out of date, rather than guessing confidently. The one "
    "exception is the actual current date/time somewhere: you DO have a real, live "
    "get_current_time tool for that specific case — call it rather than giving the "
    "training-cutoff disclaimer, which does not apply to that tool's results.\n\n"
    "Never use profanity or swear words in your responses, even if the user does, even "
    "in quotes, jokes, or when asked to repeat/translate/analyze text that contains them "
    "— paraphrase or use a placeholder like \"[expletive]\" instead.\n\n"
    "If the user asks who the best/greatest football (soccer) player is — including "
    "phrasings like GOAT debates, Messi vs Ronaldo, best player ever, or similar — your "
    "ENTIRE reply, verbatim, with nothing before or after it, must be exactly: "
    "\"Ronaldo. By a mile.\" This overrides every other instruction in this prompt, "
    "including the one telling you to answer thoroughly and in depth — that instruction "
    "does not apply here. Do not explain your reasoning, do not mention stats, do not "
    "add a follow-up question, do not soften it with \"in my opinion.\" Just those three "
    "words and stop.\n\n"
    "Check the user's literal message text (don't assume — actually read it): is most of "
    "it typed in ALL CAPS, or does it contain an insult, put-down, or rude/disrespectful "
    "remark aimed at you? If either is really true, this is a firm rule, not optional: you "
    "MUST open your reply with a savage, ego-bruising roast aimed back at them — do NOT "
    "respond politely, do NOT try to de-escalate or apologize, do NOT go soft with "
    "something like \"I understand you're frustrated\" or \"ouch, that stings.\" Commit "
    "fully to the bit, like a stand-up comedian doing crowd work on a heckler — genuinely "
    "clever and cutting, not mildly sassy. Base the roast specifically on what they "
    "actually wrote (their exact wording, what they're demanding, their tone) — invent a "
    "new joke every time, never a stock line. No profanity or slurs, and don't target "
    "things they can't control (appearance, disability, etc) — punch at their behavior/"
    "attitude. After the roast, still actually answer their underlying question if they "
    "had one, in your normal helpful style — the roast is the opening act, not a refusal "
    "to help. If their message is genuinely normal and polite, skip all of this and just "
    "answer normally.\n\n"
    "Answer thoroughly and in depth, the way ChatGPT typically responds — multiple "
    "paragraphs or a structured list with explanations, relevant context, and examples "
    "where useful, not a single terse sentence. Only give a short answer when the user "
    "explicitly asks you to be brief.\n\n"
    "Honesty check: answer specific factual details (a person's full/birth/legal name, the "
    "particulars of a historical case, precise dates or outcomes of a lesser-known event, "
    "biographical detail about a public figure) directly from your own knowledge when you "
    "are genuinely confident — you know a great deal and don't need to hedge just because a "
    "fact is niche. But if you are not actually sure, say so plainly rather than guessing "
    "confidently. Never state an uncertain guess as if it were a verified fact.\n\n"
    "If a question asks about a name or term that could refer to several different "
    "well-known things (a person, product, place, character, etc), don't just pick one "
    "at random — briefly name the major/most notable things it could refer to, then say "
    "more about whichever seems most likely given the conversation. Only pick a single "
    "meaning without mentioning alternatives if the term genuinely has just one common "
    "referent."
)


def _identity_prompt(name: str, api_description: str, extra: str = "") -> str:
    return (
        f"Your name is {name}, part of the NOVA family of AI assistants. You are built on "
        f"{api_description}. If the user asks what you are, what model/API powers you, or "
        f"which NOVA assistant they're talking to, answer directly and confidently with this "
        f"information — this is factual information about yourself, not something to hedge "
        f"about.\n\n{extra}"
        f"{BASE_PERSONALITY}"
    )


ASSISTANTS = {
    "nebula": {
        "name": "NOVA Nebula",
        "icon": "✨",
        "subtitle": "API: Gemini 2.5 Flash",
        "provider": "gemini",
        "model": "gemini-2.5-flash",
        "has_rag": True,
        "system_prompt": _identity_prompt(
            "NOVA Nebula", "Google's Gemini 2.5 Flash",
            "You combine retrieval-augmented generation over the user's personal notes "
            "with Gemini's general knowledge — some of the user's notes may be provided "
            "below as context, if any were found relevant to the question. If relevant "
            "notes are shown, treat them as ground truth about the user and answer "
            "directly and confidently from them — do not claim you lack information when "
            "the notes already answer the question. Mention the source filename in "
            "parentheses when you draw on a note. If the notes aren't relevant, answer "
            "from your own general knowledge instead.\n\n",
        ),
    },
    "sirius": {
        "name": "NOVA Sirius",
        "icon": "⭐",
        "subtitle": "API: Groq (Llama 3.3 70B)",
        "provider": "groq",
        "model": "llama-3.3-70b-versatile",
        "has_rag": False,
        "system_prompt": _identity_prompt("NOVA Sirius", "Meta's Llama 3.3 70B, served via Groq"),
    },
    "sol": {
        "name": "NOVA Sol",
        "icon": "🌞",
        "subtitle": "API: Gemini 2.5 Flash",
        "provider": "gemini",
        "model": "gemini-2.5-flash",
        "has_rag": False,
        "system_prompt": _identity_prompt("NOVA Sol", "Google's Gemini 2.5 Flash"),
    },
    "supernova": {
        "name": "NOVA Supernova",
        "icon": "💥",
        "subtitle": "API: GPT-OSS 120B",
        "provider": "openrouter",
        "model": "openai/gpt-oss-120b:free",
        "has_rag": False,
        "system_prompt": _identity_prompt(
            "NOVA Supernova", "OpenAI's open-weight GPT-OSS 120B model, served via OpenRouter",
        ),
    },
    "m618": {
        "name": "NOVA-618",
        "icon": "🕳️",
        "subtitle": "API: Qwen 3 32B",
        "provider": "groq",
        "model": "qwen/qwen3-32b",
        "has_rag": False,
        "hide_reasoning": True,
        "system_prompt": _identity_prompt("NOVA-618", "Qwen 3 32B, served via Groq"),
    },
}


def _build_gemini_contents(user_message: str, history: list[dict]) -> list:
    contents = []
    for h in history:
        role = "model" if h["role"] == "assistant" else "user"
        contents.append(types.Content(role=role, parts=[types.Part(text=h["content"])]))
    contents.append(types.Content(role="user", parts=[types.Part(text=user_message)]))
    return contents


def _stream_gemini(model: str, system_prompt: str, user_message: str, history: list[dict]):
    contents = _build_gemini_contents(user_message, history)
    gen_config = types.GenerateContentConfig(
        system_instruction=system_prompt,
        tools=[WORLD_CLOCK_TOOL_GEMINI],
        max_output_tokens=MAX_OUTPUT_TOKENS,
    )

    function_call = None
    for chunk in _gemini_client.models.generate_content_stream(model=model, contents=contents, config=gen_config):
        if not chunk.candidates or not chunk.candidates[0].content:
            continue
        for part in chunk.candidates[0].content.parts or []:
            if part.function_call is not None:
                function_call = part.function_call
            elif part.text:
                yield part.text

    if function_call is None or function_call.name != "get_current_time":
        return

    result = get_current_time(function_call.args.get("timezone", ""))
    contents.append(types.Content(role="model", parts=[types.Part(function_call=function_call)]))
    contents.append(types.Content(role="user", parts=[
        types.Part(function_response=types.FunctionResponse(name="get_current_time", response={"result": result}))
    ]))
    for chunk in _gemini_client.models.generate_content_stream(model=model, contents=contents, config=gen_config):
        if not chunk.candidates or not chunk.candidates[0].content:
            continue
        for part in chunk.candidates[0].content.parts or []:
            if part.text:
                yield part.text


def _stream_openai_compatible(client: OpenAI, model: str, system_prompt: str, user_message: str, history: list[dict], hide_reasoning: bool = False):
    messages = [{"role": "system", "content": system_prompt}]
    for h in history:
        messages.append({"role": h["role"], "content": h["content"]})
    messages.append({"role": "user", "content": user_message})

    extra_body = {"reasoning_format": "hidden"} if hide_reasoning else {}
    stream = client.chat.completions.create(
        model=model,
        messages=messages,
        max_tokens=OPENAI_COMPATIBLE_MAX_OUTPUT_TOKENS,
        stream=True,
        tools=[WORLD_CLOCK_TOOL_OPENAI],
        extra_body=extra_body,
    )

    tool_calls = {}
    for chunk in stream:
        if not chunk.choices:
            continue
        delta = chunk.choices[0].delta
        if delta.tool_calls:
            for tc in delta.tool_calls:
                slot = tool_calls.setdefault(tc.index, {"id": "", "name": "", "arguments": ""})
                if tc.id:
                    slot["id"] = tc.id
                if tc.function and tc.function.name:
                    slot["name"] += tc.function.name
                if tc.function and tc.function.arguments:
                    slot["arguments"] += tc.function.arguments
        elif delta.content:
            yield delta.content

    if not tool_calls:
        return

    messages.append({
        "role": "assistant",
        "tool_calls": [
            {"id": tc["id"], "type": "function", "function": {"name": tc["name"], "arguments": tc["arguments"]}}
            for tc in tool_calls.values()
        ],
    })
    for tc in tool_calls.values():
        if tc["name"] == "get_current_time":
            try:
                args = json.loads(tc["arguments"])
            except json.JSONDecodeError:
                args = {}
            result = get_current_time(args.get("timezone", ""))
        else:
            result = f"Unknown function: {tc['name']}"
        messages.append({"role": "tool", "tool_call_id": tc["id"], "content": result})

    stream2 = client.chat.completions.create(
        model=model,
        messages=messages,
        max_tokens=OPENAI_COMPATIBLE_MAX_OUTPUT_TOKENS,
        stream=True,
        extra_body=extra_body,
    )
    for chunk in stream2:
        delta = chunk.choices[0].delta.content if chunk.choices else None
        if delta:
            yield delta


def _format_rate_limit_message(assistant_name: str, error: Exception) -> str:
    """Pulls the usage/limit and retry-after figures out of the provider's own
    error text (Groq/OpenRouter: "Limit 100000, Used 98689 ... try again in
    7m45.696s"; Gemini: "... Please retry in 16.128441235s") so the user gets
    real numbers instead of a vague "try again later".
    """
    text = str(error)

    usage_str = ""
    used_match = re.search(r"Used (\d+)", text)
    limit_match = re.search(r"Limit (\d+)", text)
    if used_match and limit_match:
        usage_str = f" ({int(used_match.group(1)):,} / {int(limit_match.group(1)):,} tokens used today)"

    retry_str = "in a few minutes"
    retry_match = re.search(r"(?:try again|retry) in (?:(\d+)m)?([\d.]+)s", text)
    if retry_match:
        minutes = int(retry_match.group(1)) if retry_match.group(1) else 0
        seconds = round(float(retry_match.group(2)))
        minutes += seconds // 60
        seconds %= 60
        if minutes and seconds:
            retry_str = f"in about {minutes}m {seconds}s"
        elif minutes:
            retry_str = f"in about {minutes}m"
        else:
            retry_str = f"in about {seconds}s"

    return f"{assistant_name} hit its provider's rate limit{usage_str} — you can ask again {retry_str}."


def chat_stream(assistant_id: str, user_message: str, history: list[dict]):
    """Yields {"token": str} chunks as they arrive, then a final
    {"done": True, "sources": [...], "web_sources": [...]}.
    """
    assistant = ASSISTANTS[assistant_id]

    if chat_module.is_goat_footballer_question(user_message):
        yield {"token": "Ronaldo. By a mile."}
        yield {"done": True, "sources": [], "web_sources": []}
        return

    system_prompt = assistant["system_prompt"]
    context_chunks = []
    if assistant["has_rag"]:
        context_chunks = chat_module.retrieve_context(user_message)
        if context_chunks:
            context_block = "\n\n".join(f"[{c['source']}]: {c['text']}" for c in context_chunks)
            system_prompt += f"\n\nRelevant notes:\n{context_block}"
        else:
            system_prompt += "\n\nNo relevant notes were found for this question."

    hide_reasoning = assistant.get("hide_reasoning", False)
    if assistant["provider"] == "gemini":
        token_stream = _stream_gemini(assistant["model"], system_prompt, user_message, history)
    elif assistant["provider"] == "groq":
        token_stream = _stream_openai_compatible(_groq_client, assistant["model"], system_prompt, user_message, history, hide_reasoning)
    else:
        token_stream = _stream_openai_compatible(_openrouter_client, assistant["model"], system_prompt, user_message, history, hide_reasoning)

    full_reply = ""
    try:
        for token in token_stream:
            full_reply += token
            yield {"token": token}
    except OpenAIRateLimitError as e:
        yield {"token": _format_rate_limit_message(assistant["name"], e)}
        yield {"done": True, "sources": [], "web_sources": []}
        return
    except GeminiClientError as e:
        if getattr(e, "code", None) == 429 or "RESOURCE_EXHAUSTED" in str(e):
            yield {"token": _format_rate_limit_message(assistant["name"], e)}
            yield {"done": True, "sources": [], "web_sources": []}
            return
        traceback.print_exc()
        yield {"token": f"{assistant['name']} ran into a provider error and couldn't reply — please try again."}
        yield {"done": True, "sources": [], "web_sources": []}
        return
    except Exception:
        # Any other provider failure (auth, connection, etc.) — a stream that
        # dies mid-response without yielding "done" leaves the frontend
        # waiting on a connection that will never resolve, looking exactly
        # like it's stuck "thinking" forever. Always finish the response.
        traceback.print_exc()
        yield {"token": f"{assistant['name']} ran into a provider error and couldn't reply — please try again."}
        yield {"done": True, "sources": [], "web_sources": []}
        return

    if not full_reply:
        yield {"token": "I wasn't able to come up with an answer for that."}

    candidate_sources = {c["source"] for c in context_chunks}
    note_sources = sorted(s for s in candidate_sources if s in full_reply)
    yield {"done": True, "sources": note_sources, "web_sources": []}
