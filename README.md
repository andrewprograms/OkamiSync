# OkamiSync
Real-time QR-table collaborative ordering and staff dashboard for restaurants.

**OkamiSync** is an open-source, Japan-style QR-table ordering system with a mobile-first diner app and a desktop staff/admin dashboard.
It uses **FastAPI**, **PostgreSQL** (SQLAlchemy + Alembic), **Redis** (pub/sub + locks), and **vanilla HTML/CSS/JS** PWAs.
Real-time sync is handled over **WebSockets** with server-brokered rooms keyed by `table_id`.