"""Entrypoint: start the realtor cabinet (FastAPI web dashboard)."""

import uvicorn

from app.config import get_settings

if __name__ == "__main__":
    settings = get_settings()
    uvicorn.run("app.web.main:app", host=settings.web_host, port=settings.web_port, reload=False)
