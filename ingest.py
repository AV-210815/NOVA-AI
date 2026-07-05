"""Chunk notes, embed them via the Gemini API, and upsert into the local Chroma vector store.

Run directly to reindex from the CLI:
    python ingest.py
"""
import json
import re

import chromadb
from google import genai
from google.genai import types

import config

client = genai.Client(api_key=config.GEMINI_API_KEY)


def embed_texts(texts: list[str], task_type: str) -> list[list[float]]:
    """task_type is "RETRIEVAL_DOCUMENT" when embedding notes for storage, or
    "RETRIEVAL_QUERY" when embedding a search query — Gemini's embeddings are
    asymmetric and tuned for retrieval when the task types are set this way.
    """
    if not texts:
        return []
    contents = [types.Content(parts=[types.Part(text=t)]) for t in texts]
    resp = client.models.embed_content(
        model=config.EMBEDDING_MODEL,
        contents=contents,
        config=types.EmbedContentConfig(task_type=task_type),
    )
    return [e.values for e in resp.embeddings]


def get_collection():
    chroma_client = chromadb.PersistentClient(path=str(config.CHROMA_DIR))
    return chroma_client.get_or_create_collection(
        config.COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"},
    )


def load_manifest() -> dict:
    if config.MANIFEST_PATH.exists():
        return json.loads(config.MANIFEST_PATH.read_text())
    return {}


def save_manifest(manifest: dict) -> None:
    config.MANIFEST_PATH.parent.mkdir(parents=True, exist_ok=True)
    config.MANIFEST_PATH.write_text(json.dumps(manifest, indent=2))


def chunk_text(text: str, size: int = config.CHUNK_SIZE, overlap: int = config.CHUNK_OVERLAP) -> list[str]:
    """Split text into paragraphs, then greedily group paragraphs into ~size-char chunks with overlap."""
    paragraphs = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    if not paragraphs:
        return []

    chunks: list[str] = []
    current = ""
    for para in paragraphs:
        candidate = f"{current}\n\n{para}" if current else para
        if len(candidate) <= size:
            current = candidate
            continue
        if current:
            chunks.append(current)
            tail = current[-overlap:] if overlap else ""
            current = f"{tail}\n\n{para}" if tail else para
        else:
            # single paragraph longer than size: hard-split it
            for i in range(0, len(para), size - overlap):
                chunks.append(para[i:i + size])
            current = ""
    if current:
        chunks.append(current)
    return chunks


def discover_files() -> list:
    if not config.NOTES_DIR.exists():
        return []
    return [
        p for p in config.NOTES_DIR.rglob("*")
        if p.is_file() and p.suffix.lower() in config.NOTE_EXTENSIONS
    ]


def reindex() -> dict:
    collection = get_collection()
    manifest = load_manifest()

    files = discover_files()
    seen_paths = set()
    files_changed = 0
    total_chunks = 0

    for path in files:
        rel_path = str(path.relative_to(config.NOTES_DIR))
        seen_paths.add(rel_path)
        mtime = path.stat().st_mtime

        if manifest.get(rel_path, {}).get("mtime") == mtime:
            total_chunks += manifest[rel_path]["chunk_count"]
            continue

        # Remove any existing chunks for this file before re-adding
        collection.delete(where={"source": rel_path})

        text = path.read_text(encoding="utf-8", errors="ignore")
        chunks = chunk_text(text)
        if chunks:
            embeddings = embed_texts(chunks, task_type="RETRIEVAL_DOCUMENT")
            ids = [f"{rel_path}::{i}" for i in range(len(chunks))]
            metadatas = [{"source": rel_path, "chunk_index": i} for i in range(len(chunks))]
            collection.add(ids=ids, embeddings=embeddings, documents=chunks, metadatas=metadatas)

        manifest[rel_path] = {"mtime": mtime, "chunk_count": len(chunks)}
        files_changed += 1
        total_chunks += len(chunks)

    # Drop entries for files that were deleted from notes/
    removed_paths = set(manifest.keys()) - seen_paths
    for rel_path in removed_paths:
        collection.delete(where={"source": rel_path})
        del manifest[rel_path]
        files_changed += 1

    save_manifest(manifest)

    return {
        "files_indexed": len(seen_paths),
        "files_changed": files_changed,
        "total_chunks": total_chunks,
    }


if __name__ == "__main__":
    result = reindex()
    print(f"Indexed {result['files_indexed']} file(s), "
          f"{result['files_changed']} changed, "
          f"{result['total_chunks']} total chunks.")
