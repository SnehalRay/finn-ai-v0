import uuid
from fastapi import Request
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware


class RequestIDMiddleware(BaseHTTPMiddleware):
    """Injects a unique X-Request-ID header into every response for log tracing."""

    async def dispatch(self, request: Request, call_next):
        request_id = str(uuid.uuid4())
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response


def add_middleware(app) -> None:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # tighten to specific origins in production
        allow_methods=["GET", "POST"],
        allow_headers=["*"],
    )
    app.add_middleware(RequestIDMiddleware)
