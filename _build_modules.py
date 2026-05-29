"""
One-shot refactor build script.

Slices exact line ranges out of the original server.py (verbatim) and writes
them into the new pcrisk/ package, prepending a curated import header to each
module. Slicing (rather than retyping) guarantees the generated HTML/CSS and
the extraction engine remain byte-for-byte identical to the original.

This script is intended to be run once and then deleted.
"""

from pathlib import Path

ROOT = Path(__file__).resolve().parent
SRC = (ROOT / "server.py").read_text(encoding="utf-8").splitlines(keepends=True)


def sl(a: int, b: int) -> str:
    """Return server.py lines a..b inclusive (1-indexed), verbatim."""
    return "".join(SRC[a - 1:b])


def write(rel: str, header: str, body: str):
    path = ROOT / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    text = header
    if body:
        if not text.endswith("\n\n"):
            text += "\n"
        text += body
    path.write_text(text, encoding="utf-8")
    print(f"wrote {rel} ({len(text.splitlines())} lines)")


def route(*chunks: str) -> str:
    """Concatenate route slices, converting @app. decorators to @router."""
    out = []
    for c in chunks:
        out.append(c.replace("@app.", "@router."))
    return "\n".join(out)


# ----------------------------------------------------------------------------
# package markers
# ----------------------------------------------------------------------------
write("pcrisk/__init__.py", "from pcrisk.factory import create_app\n\n__all__ = [\"create_app\"]\n", "")
write("pcrisk/core/__init__.py", "", "")
write("pcrisk/ui/__init__.py", "", "")
write("pcrisk/routes/__init__.py", "", "")

# ----------------------------------------------------------------------------
# core layer
# ----------------------------------------------------------------------------
write(
    "pcrisk/core/paths.py",
    "from pathlib import Path\n\n"
    "# Project root (two levels up from pcrisk/core/paths.py).\n"
    "APP_ROOT = Path(__file__).resolve().parents[2]\n",
    sl(54, 70),
)

write(
    "pcrisk/core/config.py",
    "import json\n\n"
    "from pcrisk.core.paths import CONFIG_FILE\n",
    sl(77, 104),
)

write(
    "pcrisk/core/auth.py",
    "import hashlib\n"
    "import secrets\n"
    "import time\n"
    "from datetime import datetime\n"
    "from typing import Optional\n\n"
    "from fastapi import HTTPException, Request\n\n"
    "from pcrisk.core.config import load_config\n"
    "from pcrisk.core.paths import SESSION_COOKIE, USERS_FILE\n",
    sl(112, 310),
)

write(
    "pcrisk/core/templates.py",
    "from pathlib import Path\n"
    "from typing import Optional\n\n"
    "from pcrisk.core.paths import ASSETS_DIR, PREFERRED_TEMPLATE_FILENAME, TEMPLATE_DIR\n",
    sl(438, 501),
)

write(
    "pcrisk/core/jobs.py",
    "import json\n"
    "import re\n"
    "import threading\n"
    "import zipfile\n"
    "from datetime import datetime\n"
    "from pathlib import Path\n"
    "from typing import Optional\n\n"
    "from fastapi import HTTPException\n\n"
    "from pcrisk.core.paths import LOG_DIR, OUTPUT_DIR\n",
    sl(363, 368) + "\n\n" + sl(1426, 1602) + "\n\n" + sl(3712, 3720),
)

write(
    "pcrisk/core/cleanup.py",
    "import time\n"
    "from pathlib import Path\n"
    "from typing import Optional\n\n"
    "from pcrisk.core.config import load_config\n"
    "from pcrisk.core.paths import AUDIT_DIR, LOG_DIR, OUTPUT_DIR, UPLOAD_DIR\n",
    sl(1352, 1398),
)

# ----------------------------------------------------------------------------
# ui layer
# ----------------------------------------------------------------------------
write("pcrisk/ui/styles.py", "", sl(1609, 2615))

write(
    "pcrisk/ui/shell.py",
    "import html\n"
    "from typing import Optional\n\n"
    "from pcrisk.core.templates import get_logo_url\n"
    "from pcrisk.ui.styles import base_css\n",
    sl(2618, 2713),
)

write(
    "pcrisk/ui/pages.py",
    "import html\n"
    "import re\n"
    "from datetime import datetime\n"
    "from typing import Optional\n\n"
    "from pcrisk.core.auth import load_users\n"
    "from pcrisk.core.config import load_config\n"
    "from pcrisk.core.jobs import (\n"
    "    build_full_console_text,\n"
    "    get_file_size_label,\n"
    "    get_job_payload,\n"
    "    safe_js_json,\n"
    ")\n"
    "from pcrisk.core.paths import AUDIT_DIR, OUTPUT_DIR\n"
    "from pcrisk.core.templates import get_logo_url, get_template_status\n"
    "from pcrisk.ui.shell import head_html, hero_html, nav_html, topbar_html\n",
    sl(2720, 2766) + "\n\n" + sl(3031, 3226) + "\n\n" + sl(3227, 3352) + "\n\n" + sl(3353, 3680),
)

# ----------------------------------------------------------------------------
# automation registry + base
# ----------------------------------------------------------------------------
write("pcrisk/automations/__init__.py", "", "")

write(
    "pcrisk/automations/base.py",
    """from dataclasses import dataclass
from typing import Optional

from fastapi import APIRouter


@dataclass
class Automation:
    \"\"\"Describes a single automation that plugs into the app.

    Each automation owns its own APIRouter (its pages + processing endpoints).
    The factory mounts every registered automation's router under its
    mount_prefix. The 'primary' automation owns the root path ("/").
    \"\"\"

    slug: str
    name: str
    description: str
    router: APIRouter
    mount_prefix: str = ""
    nav_label: Optional[str] = None
    is_primary: bool = False


_REGISTRY: \"dict[str, Automation]\" = {}


def register(automation: Automation) -> Automation:
    _REGISTRY[automation.slug] = automation
    return automation


def all_automations() -> \"list[Automation]\":
    return list(_REGISTRY.values())


def get(slug: str) -> Automation:
    return _REGISTRY[slug]


def primary() -> Optional[Automation]:
    for automation in _REGISTRY.values():
        if automation.is_primary:
            return automation
    values = list(_REGISTRY.values())
    return values[0] if values else None
""",
    "",
)

# ----------------------------------------------------------------------------
# credit worksheet automation
# ----------------------------------------------------------------------------
write(
    "pcrisk/automations/credit_worksheet/__init__.py",
    "from pcrisk.automations.credit_worksheet import automation  # noqa: F401\n",
    "",
)

write(
    "pcrisk/automations/credit_worksheet/fields.py",
    "import re\n"
    "from dataclasses import dataclass, field\n"
    "from typing import Optional\n",
    sl(317, 343) + "\n\n" + sl(346, 360) + "\n\n" + sl(375, 431),
)

write(
    "pcrisk/automations/credit_worksheet/engine.py",
    "import re\n"
    "import shutil\n"
    "from dataclasses import asdict\n"
    "from datetime import datetime\n"
    "from pathlib import Path\n"
    "from typing import Optional\n\n"
    "from openpyxl import load_workbook\n\n"
    "from pcrisk.core.paths import LOG_DIR, OUTPUT_DIR, SHEET_NAME\n"
    "from pcrisk.core.templates import detect_backend_template\n"
    "from pcrisk.automations.credit_worksheet.fields import (\n"
    "    AMOUNT_PATTERN,\n"
    "    CodeOccurrence,\n"
    "    FieldResult,\n"
    "    FieldSpec,\n"
    "    FIELD_DEFINITIONS,\n"
    "    WordItem,\n"
    ")\n",
    sl(508, 1279) + "\n\n" + sl(1281, 1297),
)

write(
    "pcrisk/automations/credit_worksheet/audit.py",
    "import platform\n"
    "from datetime import datetime\n"
    "from pathlib import Path\n\n"
    "from pcrisk.core.paths import AUDIT_DIR\n"
    "from pcrisk.automations.credit_worksheet.engine import compute_field_metrics\n"
    "from pcrisk.automations.credit_worksheet.fields import FieldResult\n",
    sl(1300, 1345),
)

write(
    "pcrisk/automations/credit_worksheet/pages.py",
    "import html\n\n"
    "from pcrisk.core.config import load_config\n"
    "from pcrisk.core.templates import get_template_status\n"
    "from pcrisk.ui.shell import head_html, hero_html, topbar_html\n",
    sl(2769, 3030),
)

write(
    "pcrisk/automations/credit_worksheet/batch.py",
    "import traceback\n"
    "from datetime import datetime\n"
    "from pathlib import Path\n"
    "from typing import Optional\n\n"
    "from fastapi import UploadFile\n\n"
    "from pcrisk.core.jobs import (\n"
    "    BATCH_JOBS,\n"
    "    BATCH_JOBS_LOCK,\n"
    "    build_full_console_text,\n"
    "    create_batch_zip,\n"
    "    safe_filename,\n"
    "    save_json_debug,\n"
    "    store_job_result,\n"
    "    update_file_entry,\n"
    ")\n"
    "from pcrisk.core.paths import LOG_DIR, OUTPUT_DIR, UPLOAD_DIR\n"
    "from pcrisk.core.templates import get_template_status\n"
    "from pcrisk.automations.credit_worksheet.audit import write_audit_report\n"
    "from pcrisk.automations.credit_worksheet.engine import CreditWorksheetEngine\n",
    sl(3681, 3710) + "\n\n" + sl(3723, 3888),
)

write(
    "pcrisk/automations/credit_worksheet/routes.py",
    "import threading\n"
    "import uuid\n"
    "import traceback\n"
    "from datetime import datetime\n"
    "from pathlib import Path\n"
    "from typing import Optional\n\n"
    "from fastapi import APIRouter, File, Form, HTTPException, Request, UploadFile\n"
    "from fastapi.responses import (\n"
    "    FileResponse,\n"
    "    HTMLResponse,\n"
    "    JSONResponse,\n"
    "    RedirectResponse,\n"
    ")\n\n"
    "from pcrisk.core.auth import current_user_or_none, require_api_user\n"
    "from pcrisk.core.config import load_config\n"
    "from pcrisk.core.jobs import (\n"
    "    BATCH_JOBS,\n"
    "    BATCH_JOBS_LOCK,\n"
    "    create_batch_zip,\n"
    "    save_json_debug,\n"
    "    store_job_result,\n"
    ")\n"
    "from pcrisk.core.templates import get_template_status\n"
    "from pcrisk.automations.credit_worksheet.audit import write_audit_report\n"
    "from pcrisk.automations.credit_worksheet.batch import run_batch_job, stream_save_pdf\n"
    "from pcrisk.automations.credit_worksheet.engine import CreditWorksheetEngine\n"
    "from pcrisk.automations.credit_worksheet.pages import home_page_html\n\n"
    "router = APIRouter()\n",
    route(sl(3935, 3948), sl(4134, 4210), sl(4212, 4222), sl(4225, 4361)),
)

write(
    "pcrisk/automations/credit_worksheet/automation.py",
    """from pcrisk.automations.base import Automation, register
from pcrisk.automations.credit_worksheet.routes import router

automation = register(
    Automation(
        slug="credit_worksheet",
        name="Credit Worksheet",
        description=(
            "Upload customer PDF files and automatically produce completed "
            "Excel credit worksheets using the backend template."
        ),
        router=router,
        mount_prefix="",
        nav_label="Home",
        is_primary=True,
    )
)
""",
    "",
)

# ----------------------------------------------------------------------------
# generic routes
# ----------------------------------------------------------------------------
write(
    "pcrisk/routes/auth.py",
    "from fastapi import APIRouter, Form, Request\n"
    "from fastapi.responses import HTMLResponse, RedirectResponse\n\n"
    "from pcrisk.core.auth import (\n"
    "    authenticate,\n"
    "    create_session,\n"
    "    current_user_or_none,\n"
    "    destroy_session,\n"
    ")\n"
    "from pcrisk.core.config import load_config\n"
    "from pcrisk.core.paths import SESSION_COOKIE\n"
    "from pcrisk.ui.pages import login_page_html\n\n"
    "router = APIRouter()\n",
    route(sl(3895, 3928)),
)

write(
    "pcrisk/routes/pages.py",
    "from typing import Optional\n\n"
    "from fastapi import APIRouter, Request\n"
    "from fastapi.responses import HTMLResponse, RedirectResponse\n\n"
    "from pcrisk.core.auth import current_user_or_none\n"
    "from pcrisk.ui.pages import (\n"
    "    console_page_html,\n"
    "    outputs_page_html,\n"
    "    settings_page_html,\n"
    ")\n\n"
    "router = APIRouter()\n",
    route(sl(3951, 3972)),
)

write(
    "pcrisk/routes/settings.py",
    "from fastapi import APIRouter, Form, Request\n"
    "from fastapi.responses import RedirectResponse\n\n"
    "from pcrisk.core.auth import (\n"
    "    add_user,\n"
    "    current_user_or_none,\n"
    "    delete_user,\n"
    "    update_password,\n"
    ")\n"
    "from pcrisk.core.cleanup import force_clear_directory, run_age_based_cleanup\n"
    "from pcrisk.core.config import load_config, save_config\n"
    "from pcrisk.core.paths import AUDIT_DIR, LOG_DIR, OUTPUT_DIR, UPLOAD_DIR\n\n"
    "router = APIRouter()\n",
    route(sl(3979, 4081)),
)

write(
    "pcrisk/routes/api.py",
    "from fastapi import APIRouter, HTTPException, Request\n"
    "from fastapi.responses import FileResponse\n\n"
    "from pcrisk.core.auth import require_api_user\n"
    "from pcrisk.core.jobs import get_job_payload\n"
    "from pcrisk.core.paths import SHEET_NAME\n"
    "from pcrisk.core.templates import get_logo_path, get_logo_url, get_template_status\n"
    "from pcrisk.automations.credit_worksheet.fields import FIELD_DEFINITIONS\n\n"
    "router = APIRouter()\n",
    route(sl(4088, 4127)),
)

write(
    "pcrisk/routes/downloads.py",
    "from fastapi import APIRouter, HTTPException, Request\n"
    "from fastapi.responses import FileResponse\n\n"
    "from pcrisk.core.auth import require_api_user\n"
    "from pcrisk.core.jobs import safe_filename\n"
    "from pcrisk.core.paths import AUDIT_DIR, LOG_DIR, OUTPUT_DIR\n\n"
    "router = APIRouter()\n",
    route(sl(4368, 4411)),
)

# ----------------------------------------------------------------------------
# factory + entrypoint
# ----------------------------------------------------------------------------
write(
    "pcrisk/factory.py",
    """from fastapi import FastAPI
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
""",
    "",
)

write(
    "app.py",
    '''"""
PhillipCapital Risk Management - application entrypoint.

RUN:
    python -m uvicorn app:app --reload --host 0.0.0.0 --port 8000
"""

from pcrisk import create_app

app = create_app()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app:app", host="0.0.0.0", port=8000)
''',
    "",
)

print("DONE")
