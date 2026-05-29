from pathlib import Path
from typing import Optional

from pcrisk.core.paths import ASSETS_DIR, PREFERRED_TEMPLATE_FILENAME, TEMPLATE_DIR

def detect_backend_template() -> Path:
    preferred = TEMPLATE_DIR / PREFERRED_TEMPLATE_FILENAME

    if preferred.exists() and not preferred.name.startswith("~$"):
        return preferred

    candidates = [
        path for path in TEMPLATE_DIR.glob("*.xlsx")
        if not path.name.startswith("~$")
    ]

    if not candidates:
        raise FileNotFoundError(
            f"No Excel template found in: {TEMPLATE_DIR}. "
            "Place your blank .xlsx template inside the templates folder."
        )

    candidates.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    return candidates[0]


def get_template_status() -> dict:
    try:
        template_path = detect_backend_template()
        return {
            "exists": True,
            "filename": template_path.name,
            "folder": str(TEMPLATE_DIR),
            "path": str(template_path),
            "error": "",
        }
    except Exception as e:
        return {
            "exists": False,
            "filename": "",
            "folder": str(TEMPLATE_DIR),
            "path": "",
            "error": str(e),
        }


def get_logo_path() -> Optional[Path]:
    preferred = ASSETS_DIR / "phillipcapital_logo.png"

    if preferred.exists():
        return preferred

    candidates = [
        path for path in ASSETS_DIR.glob("*.png")
        if not path.name.startswith("~$")
    ]

    if candidates:
        candidates.sort(key=lambda p: p.stat().st_mtime, reverse=True)
        return candidates[0]

    return None


def get_logo_url() -> str:
    logo_path = get_logo_path()
    if logo_path:
        return f"/assets/{logo_path.name}"
    return ""
