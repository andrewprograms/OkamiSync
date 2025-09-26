from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, csp_default, csp_img, csp_connect):
        super().__init__(app)
        self.csp_default = csp_default
        self.csp_img = csp_img
        self.csp_connect = csp_connect

    async def dispatch(self, request: Request, call_next):
        response: Response = await call_next(request)
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['Referrer-Policy'] = 'same-origin'
        csp = (
            f"default-src {self.csp_default}; "
            f"img-src {self.csp_img}; "
            f"connect-src {self.csp_connect}; "
            "script-src 'self'; style-src 'self' 'unsafe-inline'; base-uri 'self'; form-action 'self';"
        )
        response.headers['Content-Security-Policy'] = csp
        return response
