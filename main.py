import json

from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

import chat as chat_module
import config
import ingest

app = FastAPI(title="NOVA semantic search")


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    message: str
    history: list[ChatMessage] = []


@app.post("/api/chat")
def chat(req: ChatRequest):
    history = [m.model_dump() for m in req.history]

    def event_stream():
        for chunk in chat_module.chat_stream(req.message, history):
            yield json.dumps(chunk) + "\n"

    return StreamingResponse(event_stream(), media_type="application/x-ndjson")


@app.get("/api/search")
def search(q: str, k: int = 8):
    collection = ingest.get_collection()

    if collection.count() == 0:
        return {"results": []}

    query_embedding = ingest.embed_texts([q], task_type="RETRIEVAL_QUERY")
    result = collection.query(query_embeddings=query_embedding, n_results=min(k, collection.count()))

    raw_scores = [max(0.0, 1 - distance / 2) for distance in result["distances"][0]]
    lo, hi = min(raw_scores), max(raw_scores)
    spread = hi - lo

    results = []
    for doc, meta, raw_score in zip(result["documents"][0], result["metadatas"][0], raw_scores):
        # Rescale within this result set: best match -> 1.0, worst shown -> 0.0.
        # Raw cosine similarity from sentence embeddings clusters in a high, non-zero
        # band even for unrelated text, so an absolute score is misleading as a "% match".
        relative_score = (raw_score - lo) / spread if spread > 1e-9 else 1.0
        results.append({
            "text": doc,
            "source": meta["source"],
            "chunk_index": meta["chunk_index"],
            "score": round(relative_score, 4),
        })
    return {"results": results}


@app.post("/api/reindex")
def reindex():
    return ingest.reindex()


@app.get("/api/stats")
def stats():
    collection = ingest.get_collection()
    manifest = ingest.load_manifest()
    return {"total_chunks": collection.count(), "total_files": len(manifest)}


app.mount("/", StaticFiles(directory=str(config.BASE_DIR / "static"), html=True), name="static")
