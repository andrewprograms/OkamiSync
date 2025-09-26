import time, hmac, hashlib, base64, os
from fastapi import HTTPException
from starlette.responses import FileResponse
from app.config import settings

def _sign(path: str, exp: int) -> str:
    raw = f"{path}:{exp}".encode()
    sig = hmac.new(settings.media_sign_key.encode(), raw, hashlib.sha256).digest()
    return base64.urlsafe_b64encode(sig).decode().rstrip('=')

def gen_signed_url(path: str, ttl: int = 3600) -> str:
    exp = int(time.time()) + ttl
    sig = _sign(path, exp)
    return f"{settings.media_base_url}/{path}?e={exp}&sig={sig}"

def verify_and_serve(path: str, e: int, sig: str):
    if not path or ".." in path:
        raise HTTPException(400, "bad path")
    expect = _sign(path, e)
    if not hmac.compare_digest(expect, sig or "") or int(time.time()) > int(e):
        raise HTTPException(403, "expired or invalid signature")
    file_path = os.path.join(settings.media_root, path)
    if not os.path.isfile(file_path):
        raise HTTPException(404, "file not found")
    return FileResponse(file_path)
