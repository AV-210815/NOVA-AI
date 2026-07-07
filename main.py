import json
import os
from datetime import datetime, timezone

from fastapi import Cookie, Depends, FastAPI, File, Form, HTTPException, Response, UploadFile
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

import assistants
import auth
import config
import db
import health
import ingest
import voice

db.init_db()

app = FastAPI(title="NOVA semantic search")


def require_user(nova_session: str | None = Cookie(default=None)) -> dict:
    user = auth.get_current_user(nova_session)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return user


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    message: str
    history: list[ChatMessage] = []
    assistant: str = "nebula"


class DeleteHealthEntryRequest(BaseModel):
    timestamp: str


class GoogleLoginRequest(BaseModel):
    credential: str


class SaveChatRequest(BaseModel):
    id: str
    title: str
    messages: list[dict]
    assistant: str = "nebula"


def _public_user(user: dict) -> dict:
    return {"email": user["email"], "name": user["name"], "picture": user["picture"]}


@app.get("/api/auth/config")
def auth_config():
    return {"client_id": config.GOOGLE_OAUTH_CLIENT_ID}


@app.post("/api/auth/google")
def auth_google(req: GoogleLoginRequest, response: Response):
    try:
        session_token, user = auth.login_with_google_token(req.credential)
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))
    response.set_cookie(
        key=auth.SESSION_COOKIE,
        value=session_token,
        httponly=True,
        samesite="lax",
        secure=bool(os.environ.get("RENDER")),
        max_age=db.SESSION_LIFETIME_SECONDS,
    )
    return _public_user(user)


@app.post("/api/auth/logout")
def auth_logout(response: Response, nova_session: str | None = Cookie(default=None)):
    if nova_session:
        db.delete_session(nova_session)
    response.delete_cookie(auth.SESSION_COOKIE)
    return {"ok": True}


@app.get("/api/auth/me")
def auth_me(nova_session: str | None = Cookie(default=None)):
    user = auth.get_current_user(nova_session)
    return {"user": _public_user(user) if user else None}


@app.get("/api/assistants")
def assistants_list():
    return {
        "assistants": [
            {"id": aid, "name": a["name"], "icon": a["icon"], "subtitle": a["subtitle"]}
            for aid, a in assistants.ASSISTANTS.items()
        ]
    }


@app.post("/api/chat")
def chat(req: ChatRequest, user: dict = Depends(require_user)):
    history = [m.model_dump() for m in req.history]
    assistant_id = req.assistant if req.assistant in assistants.ASSISTANTS else "nebula"

    def event_stream():
        for chunk in assistants.chat_stream(assistant_id, req.message, history):
            yield json.dumps(chunk) + "\n"

    return StreamingResponse(event_stream(), media_type="application/x-ndjson")


@app.get("/api/chats")
def chats_list(assistant: str = "nebula", user: dict = Depends(require_user)):
    return {"chats": db.list_chats(user["id"], assistant)}


@app.get("/api/chats/{chat_id}")
def chats_get(chat_id: str, assistant: str = "nebula", user: dict = Depends(require_user)):
    chat_data = db.get_chat(user["id"], assistant, chat_id)
    if not chat_data:
        raise HTTPException(status_code=404, detail="Chat not found")
    return chat_data


@app.post("/api/chats")
def chats_save(req: SaveChatRequest, user: dict = Depends(require_user)):
    db.save_chat(user["id"], req.assistant, req.id, req.title, req.messages)
    return {"ok": True}


@app.delete("/api/chats/{chat_id}")
def chats_delete(chat_id: str, assistant: str = "nebula", user: dict = Depends(require_user)):
    db.delete_chat(user["id"], assistant, chat_id)
    return {"ok": True}


@app.get("/api/search")
def search(q: str, k: int = 8, user: dict = Depends(require_user)):
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


@app.post("/api/transcribe")
async def transcribe(audio: UploadFile = File(...), user: dict = Depends(require_user)):
    audio_bytes = await audio.read()
    text = voice.transcribe_audio(audio_bytes)
    return {"text": text}


@app.post("/api/health/analyze")
async def health_analyze(
    message: str = Form(""),
    history: str = Form("[]"),
    image: UploadFile | None = File(None),
    user: dict = Depends(require_user),
):
    history_list = json.loads(history)
    image_bytes = await image.read() if image is not None else None
    mime_type = image.content_type if image is not None else None

    def event_stream():
        for chunk in health.analyze_food(user["id"], message, history_list, image_bytes, mime_type):
            yield json.dumps(chunk) + "\n"

    return StreamingResponse(event_stream(), media_type="application/x-ndjson")


@app.get("/api/health/log")
def health_log(user: dict = Depends(require_user)):
    entries = db.load_health_entries(user["id"])
    today = datetime.now(timezone.utc).date().isoformat()
    today_total = sum(e["calories"] for e in entries if e["timestamp"].startswith(today))
    return {"entries": entries, "today_total_calories": today_total}


@app.post("/api/health/log/delete")
def health_log_delete(req: DeleteHealthEntryRequest, user: dict = Depends(require_user)):
    deleted = db.delete_health_entry(user["id"], req.timestamp)
    return {"deleted": deleted}


@app.post("/api/reindex")
def reindex(user: dict = Depends(require_user)):
    return ingest.reindex()


@app.get("/api/stats")
def stats(user: dict = Depends(require_user)):
    collection = ingest.get_collection()
    manifest = ingest.load_manifest()
    return {"total_chunks": collection.count(), "total_files": len(manifest)}


app.mount("/", StaticFiles(directory=str(config.BASE_DIR / "static"), html=True), name="static")
