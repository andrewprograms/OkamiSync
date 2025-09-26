from fastapi import HTTPException, Request
from app.auth.sessions import read_session

def staff_required(request: Request):
    sess = read_session(request)
    if not sess:
        raise HTTPException(status_code=401, detail="Not authenticated")
    if sess.get("role") not in ("staff", "admin"):
        raise HTTPException(status_code=403, detail="Forbidden")
    return sess

def admin_required(request: Request):
    sess = read_session(request)
    if not sess:
        raise HTTPException(status_code=401, detail="Not authenticated")
    if sess.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Forbidden")
    return sess
