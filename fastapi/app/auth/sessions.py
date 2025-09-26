import secrets, json, base64
from typing import Optional
from fastapi import Request, Response
from itsdangerous import TimestampSigner, BadSignature, SignatureExpired
from app.config import settings

signer = TimestampSigner(settings.session_secret)

SESSION_COOKIE = "nq_sess"
CSRF_COOKIE = "nq_csrf"

def _b64e(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode().rstrip('=')

def _b64d(s: str) -> bytes:
    pad = '=' * (-len(s) % 4)
    return base64.urlsafe_b64decode(s + pad)

def set_csrf_cookie(response: Response, token: str):
    response.set_cookie(CSRF_COOKIE, token, httponly=False, samesite="Strict", secure=True)

def new_csrf_token() -> str:
    return secrets.token_urlsafe(32)

def require_csrf(request: Request):
    if request.method in ("GET", "HEAD", "OPTIONS"):
        return
    cookie = request.cookies.get(CSRF_COOKIE)
    header = request.headers.get("X-CSRF-Token")
    if not cookie or not header or cookie != header:
        from fastapi import HTTPException
        raise HTTPException(status_code=403, detail="CSRF check failed")

def create_session(response: Response, user_id: str, role: str):
    payload = json.dumps({"uid": user_id, "role": role}).encode()
    signed = signer.sign(payload)
    response.set_cookie(
        SESSION_COOKIE,
        _b64e(signed),
        httponly=True,
        samesite="Strict",
        secure=True,
        domain=settings.cookie_domain,
        path="/",
    )

def read_session(request: Request) -> Optional[dict]:
    raw = request.cookies.get(SESSION_COOKIE)
    if not raw:
        return None
    try:
        signed = _b64d(raw)
        payload = signer.unsign(signed, max_age=60*60*8)
        return json.loads(payload.decode())
    except (BadSignature, SignatureExpired):
        return None

def destroy_session(response: Response):
    response.delete_cookie(SESSION_COOKIE, path="/")
