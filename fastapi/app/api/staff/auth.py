from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
import uuid
from app.db import get_async_session
from app.models.users import User
from app.auth.passwords import verify_password
from app.auth.sessions import create_session, destroy_session, new_csrf_token, set_csrf_cookie
from app.schemas.staff import StaffLoginIn

router = APIRouter(prefix="/api/staff", tags=["staff"])

@router.post("/login")
async def staff_login(payload: StaffLoginIn, response: Response, session: AsyncSession = Depends(get_async_session)):
    res = await session.execute(select(User).where(User.username==payload.username))
    user = res.scalar_one_or_none()
    if not user or not user.active or not verify_password(payload.password, user.password_hash):
        raise HTTPException(401, "Invalid credentials")
    create_session(response, user_id=user.id, role=user.role)
    set_csrf_cookie(response, new_csrf_token())
    return {"ok": True, "role": user.role}

@router.post("/logout")
async def staff_logout(response: Response):
    destroy_session(response)
    return {"ok": True}
