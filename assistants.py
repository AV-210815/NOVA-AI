"""The NOVA family: multiple chat assistants backed by different models/providers.

Each one shares the same base personality (thorough answers, no profanity, roasts
back if the user is rude, an honesty calibration policy, and a running joke about
football GOAT debates) but identifies itself correctly by its own name/model, and
is backed by its own provider. NOVA Nebula is the only one with retrieval-augmented
generation over the user's notes — the others are plain conversational chat.
"""
from openai import OpenAI

from google import genai
from google.genai import types

import chat as chat_module
import config

_gemini_client = genai.Client(api_key=config.GEMINI_API_KEY)
_groq_client = OpenAI(api_key=config.GROQ_API_KEY, base_url="https://api.groq.com/openai/v1")
_openrouter_client = OpenAI(api_key=config.OPENROUTER_API_KEY, base_url="https://openrouter.ai/api/v1")

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
    "and the answer may be out of date, rather than guessing confidently.\n\n"
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
        max_output_tokens=MAX_OUTPUT_TOKENS,
    )
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
        extra_body=extra_body,
    )
    for chunk in stream:
        delta = chunk.choices[0].delta.content if chunk.choices else None
        if delta:
            yield delta


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
    for token in token_stream:
        full_reply += token
        yield {"token": token}

    if not full_reply:
        yield {"token": "I wasn't able to come up with an answer for that."}

    candidate_sources = {c["source"] for c in context_chunks}
    note_sources = sorted(s for s in candidate_sources if s in full_reply)
    yield {"done": True, "sources": note_sources, "web_sources": []}
