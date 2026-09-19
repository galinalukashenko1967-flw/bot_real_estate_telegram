"""Entrypoint: start the realtor cabinet (FastAPI web dashboard)."""

import os

import uvicorn

from app.config import get_settings

if __name__ == "__main__":
    settings = get_settings()
    # Railway (and most PaaS providers) assign the public port at runtime via
    # the PORT env var and ignore whatever the app asks for, so it takes
    # priority over WEB_PORT when set.
    port = int(os.environ.get("PORT", settings.web_port))
    uvicorn.run("app.web.main:app", host=settings.web_host, port=port, reload=False)
