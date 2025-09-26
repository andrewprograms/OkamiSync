# Security & Threat Model

## Trust Boundaries
- **Client (diner PWA)**: Untrusted. Anonymous device IDs stored in `localStorage`. Never embeds secrets.
- **Staff/Admin dashboard**: Trusted authenticated users via httpOnly session cookie. CSRF protected and origin-locked.
- **Backend (FastAPI)**: Trusted. Holds all signing keys, credentials, and authorization logic.
- **Redis**: Trusted infra for ephemeral locks and pub/sub. Do not store PII beyond anon IDs.
- **PostgreSQL**: Trusted persistent store.

## Common Abuse Cases & Mitigations
- **Ordering for another table**: Every public call requires (1) *table token* and (2) short-lived *session capability* bound to `table_id` and `session_id`. Server verifies both on every write. WebSocket room joins validate origin and token. No cross-table lookups are permitted.
- **Replay/double submit**: All mutation endpoints require an `Idempotency-Key` header; server stores computed result in Redis. Carts use short Redis locks to avoid racey duplicates.
- **Menu scraping**: Menu is public by design; you may rate-limit `/api/public/menu` and enable ETags. Media served via signed URLs to prevent hotlinking.
- **Token reuse**: QR encodes an opaque table ID only; capability (`session_cap`) rotates per device with ~10-minute expiry, and is refreshed when the page is reloaded.
- **XSS/Injection**: All freeform text (notes, reasons) is sanitized and length-constrained. Output is escaped by default. CSP is set to restrict sources; no inline scripts except controlled CSS.
- **CSRF**: Staff/Admin endpoints require an `X-CSRF-Token` header matching a cookie; all write paths enforce server-side checks. Public endpoints are token-gated and same-origin only.
- **Origin checks**: WebSocket upgrades validate `Origin` against `CORS_ALLOWLIST`.
- **Secrets**: Stored only in server environment (`.env`). Never logged. Authentication events and admin changes are logged without tokens.
- **Rate Limiting**: Public endpoints are rate limited via SlowAPI; repeated failures should backoff on client.
- **GDPR-style hygiene**: No PII for diners; only ephemeral anon IDs and device IDs. Staff audit logs include user IDs but no credentials.

## Additional Hardening
- Serve behind TLS + HSTS; set Secure cookies only over HTTPS.
- Use a reverse proxy (e.g., Nginx) to terminate TLS and enforce size limits, gzip, and caching of static files.
- Turn on DB row-level security if you extend per-tenant support.
- Rotate HMAC keys periodically (K1->K0). Reissue session capabilities on rotation.