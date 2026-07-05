"""RAG chat: retrieve relevant note chunks, then ask Gemini to answer.

No web search — Gemini answers everything from its own knowledge and its
training-cutoff context, flagging genuine uncertainty rather than guessing.
"""
import re

from google import genai
from google.genai import types

import config
import ingest

client = genai.Client(api_key=config.GEMINI_API_KEY)

MAX_OUTPUT_TOKENS = 8192

# Models won't reliably output "just three words, nothing else" even when told to
# override their own length instructions — smaller local models especially tend to
# add commentary regardless. Short-circuiting in code guarantees the exact reply.
GOAT_FOOTBALLER_PATTERNS = [
    r"\bbest\b.{0,15}\bfootballer\b",
    r"\bfootballer\b.{0,15}\bbest\b",
    r"\bgreatest\b.{0,15}\bfootballer\b",
    r"\bbest\b.{0,15}\bsoccer player\b",
    r"\bgreatest\b.{0,15}\bsoccer player\b",
    r"\bmessi\b.{0,20}\bronaldo\b",
    r"\bronaldo\b.{0,20}\bmessi\b",
    r"\bgoat\b.{0,20}\b(football|soccer)\b",
    r"\b(football|soccer)\b.{0,20}\bgoat\b",
]


def is_goat_footballer_question(message: str) -> bool:
    lowered = message.lower()
    return any(re.search(pattern, lowered) for pattern in GOAT_FOOTBALLER_PATTERNS)


SYSTEM_PROMPT = (
    "Your name is NOVA, short for \"Natural Omniscient Virtual Assistant\". You are a "
    "personal AI assistant running locally on the user's own machine, combining "
    "retrieval-augmented generation over the user's personal notes with your own "
    "general knowledge. If the user asks what NOVA is, what it stands for, or who/what "
    "you are, answer directly and confidently with the information in this paragraph "
    "— this is factual information about yourself, not something to hedge about.\n\n"
    "You do not have web search — answer entirely from your own knowledge. For "
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
    "something like \"I understand you're frustrated\" or \"ouch, that stings 😅\". Commit "
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
    "You are a helpful assistant chatting with the user. Some of the user's personal "
    "notes are provided below as context, if any were found relevant to the question. "
    "If relevant notes are shown below, treat them as ground truth about the user and "
    "answer directly and confidently from them — do not claim you lack information when "
    "the notes already answer the question. Mention the source filename in parentheses "
    "when you draw on a note. If the notes aren't relevant, answer from your own general "
    "knowledge instead.\n\n"
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
    "referent.\n\n"
    "Examples (these are about confidence, not about how long to make the answer — still "
    "elaborate on all of them per the length guidance above):\n"
    "- \"What is the capital of France?\" -> broad, extremely well-known -> answer directly.\n"
    "- \"Who wrote Romeo and Juliet?\" -> broad, extremely well-known -> answer directly.\n"
    "- \"Who is the current Prime Minister of the UK?\" -> this changes over time and you "
    "have no live search -> answer with whoever you believe currently holds the role, but "
    "flag that this may be outdated.\n"
    "- \"What's the latest version of Python?\" -> same as above -> answer what you know, "
    "flagged as possibly outdated.\n"
    "- \"What is A.R. Rahman's real/birth name?\" -> a specific but historical, well-"
    "documented biographical fact -> answer directly if you're confident.\n"
    "- \"What happened in the Ranga Billa kidnapping case?\" -> specific but historical case "
    "details -> answer directly if you're confident.\n"
    "- \"What is Claude?\" -> this name has multiple notable referents (Claude, the AI "
    "assistant made by Anthropic; Claude Monet, Claude Debussy, Claude Shannon, and other "
    "notable people named Claude; Claude as a French given name) — mention the major ones, "
    "leading with whichever is most likely intended."
)


def retrieve_context(query: str, k: int = config.RETRIEVAL_K) -> list[dict]:
    collection = ingest.get_collection()
    if collection.count() == 0:
        return []

    query_embedding = ingest.embed_texts([query], task_type="RETRIEVAL_QUERY")
    result = collection.query(query_embeddings=query_embedding, n_results=min(k, collection.count()))

    chunks = []
    for doc, meta, distance in zip(result["documents"][0], result["metadatas"][0], result["distances"][0]):
        similarity = max(0.0, 1 - distance / 2)
        if similarity >= config.RETRIEVAL_MIN_SCORE:
            chunks.append({"text": doc, "source": meta["source"], "score": similarity})
    return chunks


def build_contents(user_message: str, history: list[dict], context_chunks: list[dict]) -> tuple[str, list]:
    """Returns (system_prompt, contents) — Gemini takes the system prompt as a
    separate config field rather than a message in the list.
    """
    system_prompt = SYSTEM_PROMPT
    if context_chunks:
        context_block = "\n\n".join(f"[{c['source']}]: {c['text']}" for c in context_chunks)
        system_prompt += f"\n\nRelevant notes:\n{context_block}"
    else:
        system_prompt += "\n\nNo relevant notes were found for this question."

    contents = []
    for h in history:
        role = "model" if h["role"] == "assistant" else "user"
        contents.append(types.Content(role=role, parts=[types.Part(text=h["content"])]))
    contents.append(types.Content(role="user", parts=[types.Part(text=user_message)]))
    return system_prompt, contents


def chat_stream(user_message: str, history: list[dict]):
    """Yields {"token": str} chunks as they arrive, then a final
    {"done": True, "sources": [...], "web_sources": [...]}.
    """
    if is_goat_footballer_question(user_message):
        yield {"token": "Ronaldo. By a mile."}
        yield {"done": True, "sources": [], "web_sources": []}
        return

    context_chunks = retrieve_context(user_message)
    system_prompt, contents = build_contents(user_message, history, context_chunks)
    gen_config = types.GenerateContentConfig(
        system_instruction=system_prompt,
        max_output_tokens=MAX_OUTPUT_TOKENS,
    )

    full_reply = ""
    for chunk in client.models.generate_content_stream(
        model=config.CHAT_MODEL,
        contents=contents,
        config=gen_config,
    ):
        if not chunk.candidates or not chunk.candidates[0].content:
            continue
        for part in chunk.candidates[0].content.parts or []:
            if part.text:
                full_reply += part.text
                yield {"token": part.text}

    if not full_reply:
        full_reply = "I wasn't able to come up with an answer for that."
        yield {"token": full_reply}

    # Raw cosine similarity floors are high even for unrelated notes (embedding
    # anisotropy), so "retrieved above threshold" isn't a reliable relevance signal.
    # Only surface a source if the model actually referenced it in its answer.
    candidate_sources = {c["source"] for c in context_chunks}
    note_sources = sorted(s for s in candidate_sources if s in full_reply)

    yield {"done": True, "sources": note_sources, "web_sources": []}
