"""Google Sign-In: verify the ID token from Google Identity Services, then
issue our own opaque session cookie so we don't re-verify with Google on
every request.
"""
from google.auth.transport import requests as google_requests
from google.oauth2 import id_token

import config
import db

SESSION_COOKIE = "nova_session"

_google_request = google_requests.Request()


def verify_google_id_token(token: str) -> dict:
    """Raises ValueError if the token is invalid, expired, or for the wrong audience."""
    return id_token.verify_oauth2_token(token, _google_request, audience=config.GOOGLE_OAUTH_CLIENT_ID)


def login_with_google_token(token: str) -> tuple[str, dict]:
    """Verifies the token, upserts the user, and returns (session_token, user_dict)."""
    claims = verify_google_id_token(token)
    user = db.upsert_user(
        google_sub=claims["sub"],
        email=claims.get("email", ""),
        name=claims.get("name", ""),
        picture=claims.get("picture", ""),
    )
    session_token = db.create_session(user["id"])
    return session_token, dict(user)


def get_current_user(session_cookie: str | None) -> dict | None:
    row = db.get_user_by_session(session_cookie)
    return dict(row) if row else None
