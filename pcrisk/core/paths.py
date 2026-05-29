from pathlib import Path

# Project root (two levels up from pcrisk/core/paths.py).
APP_ROOT = Path(__file__).resolve().parents[2]

TEMPLATE_DIR = APP_ROOT / "templates"
UPLOAD_DIR = APP_ROOT / "uploads"
OUTPUT_DIR = APP_ROOT / "outputs"
LOG_DIR = APP_ROOT / "logs"
ASSETS_DIR = APP_ROOT / "assets"
AUDIT_DIR = APP_ROOT / "audits"

USERS_FILE = APP_ROOT / "users.json"
CONFIG_FILE = APP_ROOT / "app_config.json"

SHEET_NAME = "Sheet1"
PREFERRED_TEMPLATE_FILENAME = "Buckler Excel Credit WS Template.xlsx"

SESSION_COOKIE = "pc_session"

for folder in [TEMPLATE_DIR, UPLOAD_DIR, OUTPUT_DIR, LOG_DIR, ASSETS_DIR, AUDIT_DIR]:
    folder.mkdir(parents=True, exist_ok=True)
