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
EMBEDDING_MODEL = "all-MiniLM-L6-v2"

CHUNK_SIZE = 500
CHUNK_OVERLAP = 50

NOTE_EXTENSIONS = {".md", ".txt"}

CHAT_MODEL = "gemini-2.5-flash"

RETRIEVAL_K = 5

# Raw cosine similarity floor below which a chunk isn't worth citing. Sentence
# embeddings are anisotropic: even unrelated chunks score ~0.5-0.65, while chunks
# genuinely relevant to the query have scored 0.7+ in testing. 0.35 let irrelevant
# notes leak into every prompt; 0.65 tracks the observed gap much more closely.
RETRIEVAL_MIN_SCORE = 0.65

# Gemini API key (Google AI Studio).
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
