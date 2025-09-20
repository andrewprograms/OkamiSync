import time, json, hmac, hashlib, base64, re
from typing import Optional
from app.config import settings

def _b64e(b: bytes) -> str:
    return base64.urlsafe_b64encode(b).decode().rstrip('=')

def _b64d(s: str) -> bytes:
    pad = '=' * (-len(s) % 4)
    return base64.urlsafe_b64decode(s + pad)

def sign(payload: dict, key: str) -> str:
    body = json.dumps(payload, separators=(',', ':'), sort_keys=True).encode()
    sig = hmac.new(key.encode(), body, hashlib.sha256).digest()
    return _b64e(body) + "." + _b64e(sig)

def verify(token: str, keys: list[str]) -> Optional[dict]:
    try:
        body_b64, sig_b64 = token.split(".", 1)
        body = _b64d(body_b64)
        for k in keys:
            expect = hmac.new(k.encode(), body, hashlib.sha256).digest()
            if hmac.compare_digest(expect, _b64d(sig_b64)):
                return json.loads(body.decode())
        return None
    except Exception:
        return None

def issue_table_token(opaque_table_uid: str) -> str:
    payload = {"tab": opaque_table_uid, "iat": int(time.time())}
    return sign(payload, settings.token_key_k1)

def parse_table_token(token: str) -> Optional[dict]:
    return verify(token, [settings.token_key_k1, settings.token_key_k0])

# Helper: accept signed token, JSON (with {"tab": ...}), or raw opaque UID
_ALLOWED_OPAQUE = re.compile(r"^[A-Za-z0-9_-]{8,64}$")

def extract_opaque(token_or_raw: str) -> Optional[str]:
    if not token_or_raw:
        return None
    # Signed?
    data = parse_table_token(token_or_raw)
    if data and "tab" in data:
        return data["tab"]
    # JSON-ish (bootstrap from client)?
    try:
        j = json.loads(token_or_raw)
        if isinstance(j, dict) and "tab" in j and _ALLOWED_OPAQUE.match(j["tab"] or ""):
            return j["tab"]
    except Exception:
        pass
    # Raw opaque?
    if _ALLOWED_OPAQUE.match(token_or_raw):
        return token_or_raw
    return None

def issue_session_cap(table_id: int, session_id: str, ttl_seconds: int = 600) -> str:
    now = int(time.time())
    payload = {"tid": table_id, "sid": session_id, "iat": now, "exp": now + ttl_seconds}
    return sign(payload, settings.session_secret)

def verify_session_cap(token: str) -> Optional[dict]:
    data = verify(token, [settings.session_secret])
    if not data:
        return None
    now = int(time.time())
    if data.get("exp", 0) < now:
        return None
    return data
