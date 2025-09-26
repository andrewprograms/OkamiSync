import os
from fastapi import FastAPI, Request, Response, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.middleware.security_headers import SecurityHeadersMiddleware
from app.rate_limit import limiter, SlowAPIMiddleware
from app.api.public import router as public_router
from app.api.public.session import router as public_session_router
from app.api.public.menu import router as public_menu_router
from app.api.public.cart import router as public_cart_router
from app.api.staff import router as staff_router
from app.api.staff.auth import router as staff_auth_router
from app.api.staff.orders import router as staff_orders_router
from app.api.admin import router as admin_router
from app.api.admin.menu import router as admin_menu_router
from app.ws.routes import router as ws_router
from app.auth.sessions import new_csrf_token, set_csrf_cookie
from app.db import get_async_session
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.tables import Table

app = FastAPI(title=settings.app_name)

# Middleware
origins = [o.strip() for o in settings.cors_allowlist.split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)
app.add_middleware(
    SecurityHeadersMiddleware,
    csp_default=settings.csp_default_src,
    csp_img=settings.csp_img_src,
    csp_connect=settings.csp_connect_src
)
app.add_middleware(SlowAPIMiddleware)

# Routers
app.include_router(public_router)
app.include_router(public_session_router)
app.include_router(public_menu_router)
app.include_router(public_cart_router)
app.include_router(staff_router)
app.include_router(staff_auth_router)
app.include_router(staff_orders_router)
app.include_router(admin_router)
app.include_router(admin_menu_router)
app.include_router(ws_router)

# Static (PWA) apps
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/", response_class=HTMLResponse)
async def home():
    return HTMLResponse('<h1>NorenQR</h1><p>Use /staff for dashboard or scan a table QR from ./qr.</p>')

@app.get("/t/{opaque}", response_class=HTMLResponse)
async def table_entry(opaque: str, request: Request, response: Response, session: AsyncSession = Depends(get_async_session)):
    # Validate opaque token -> table exists
    res = await session.execute(select(Table).where(Table.opaque_uid == opaque))
    table = res.scalar_one_or_none()
    if not table:
        return HTMLResponse("<h1>Invalid table</h1>", status_code=404)
    # Serve the table app
    html = open("static/table/index.html", "r", encoding="utf-8").read()
    return HTMLResponse(html)

@app.get("/staff/", response_class=HTMLResponse)
async def staff_page(response: Response):
    set_csrf_cookie(response, new_csrf_token())
    html = open("static/staff/dashboard.html", "r", encoding="utf-8").read()
    return HTMLResponse(html)

@app.get("/admin/", response_class=HTMLResponse)
async def admin_page(response: Response):
    set_csrf_cookie(response, new_csrf_token())
    html = open("static/staff/admin.html", "r", encoding="utf-8").read()
    return HTMLResponse(html)

# Signed-media proxy
from fastapi import Query
from app.services.media_proxy import verify_and_serve

@app.get("/media/{path:path}")
async def media_proxy(path: str, e: int = Query(...), sig: str = Query(...)):
    return verify_and_serve(path, e, sig)
