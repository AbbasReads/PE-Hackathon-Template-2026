from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.routes import events, health, urls, users


def create_app() -> FastAPI:
    app = FastAPI(title="Hackathon URL Shortener")

    @app.exception_handler(Exception)
    async def handle_unexpected_error(_request: Request, _exc: Exception) -> JSONResponse:
        return JSONResponse(status_code=500, content={"detail": "Internal Server Error"})

    app.include_router(health.router)
    app.include_router(users.router)
    app.include_router(urls.router)
    app.include_router(events.router)
    return app
