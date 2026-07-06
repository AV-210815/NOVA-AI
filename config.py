import os
from pathlib import Path

BASE_DIR = Path(__file__).parent


def _load_dotenv(path: Path) -> None:
    """Minimal .env loader — avoids adding a python-dotenv dependency for two vars.

    Only sets a variable if it isn't already set in the real environment, so an
    explicit `export` always wins over the file.
    """
    if not path.exists():
        return
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key, value = key.strip(), value.strip().strip('"').strip("'")
        os.environ.setdefault(key, value)


_load_dotenv(BASE_DIR / ".env")
NOTES_DIR = BASE_DIR / "notes"
CHROMA_DIR = BASE_DIR / ".chroma"
MANIFEST_PATH = BASE_DIR / ".chroma" / "manifest.json"

COLLECTION_NAME = "notes"
# Switched from local sentence-transformers (all-MiniLM-L6-v2) to Gemini's hosted
# embedding API — removes the PyTorch dependency, which was too heavy for Render's
# free-tier RAM limit.
EMBEDDING_MODEL = "gemini-embedding-2"

CHUNK_SIZE = 500
CHUNK_OVERLAP = 50

NOTE_EXTENSIONS = {".md", ".txt"}

CHAT_MODEL = "gemini-2.5-flash"

RETRIEVAL_K = 5

# Raw cosine similarity floor below which a chunk isn't worth citing. Re-calibrated
# for gemini-embedding-2: unrelated queries scored ~0.75-0.77 in testing, genuinely
# relevant ones ~0.78-0.83 — a narrower gap than all-MiniLM had, so the floor sits
# right above the irrelevant band rather than in the middle of a wide one.
RETRIEVAL_MIN_SCORE = 0.78

# Gemini API key (Google AI Studio).
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")

# Local Whisper model size for voice input transcription. "base" balances accuracy
# against memory/CPU — this pulls in PyTorch (like the old local embeddings did),
# so it's a real memory risk on Render's free tier; fine for local use.
WHISPER_MODEL = "base"

# NOVA Health: photo-based food/calorie tracking. Gemini's own vision input
# handles the image analysis, so no separate vision model/dependency is needed.
HEALTH_LOG_PATH = BASE_DIR / "health_log.json"
