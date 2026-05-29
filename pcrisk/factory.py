from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from pcrisk.core import auth as _auth  # noqa: F401  (import seeds preset users)
from pcrisk.core.cleanup import run_age_based_cleanup
from pcrisk.core.paths import ASSETS_DIR
from pcrisk.routes import api as api_routes
from pcrisk.routes import auth as auth_routes
from pcrisk.routes import downloads as downloads_routes
from pcrisk.routes import pages as pages_routes
from pcrisk.routes import settings as settings_routes
from pcrisk.automations import base as registry

# Importing the automations package registers every automation.
import pcrisk.automations.credit_worksheet  # noqa: F401


def create_app() -> FastAPI:
    app = FastAPI(
        title="PhillipCapital Risk Management Credit Worksheet Processor",
        description="FastAPI PDF-to-Excel processor for Risk Management credit worksheet automation.",
        version="7.0.0",
    )

    app.mount("/assets", StaticFiles(directory=str(ASSETS_DIR)), name="assets")

    @app.on_event("startup")
    def on_startup():
        try:
            run_age_based_cleanup()
        except Exception:
            pass

    # Shared/cross-automation routes.
    app.include_router(auth_routes.router)
    app.include_router(pages_routes.router)
    app.include_router(settings_routes.router)
    app.include_router(api_routes.router)
    app.include_router(downloads_routes.router)

    # Per-automation routes (pages + processing endpoints).
    for automation in registry.all_automations():
        app.include_router(automation.router, prefix=automation.mount_prefix)

    return app
