import json

from pcrisk.core.paths import CONFIG_FILE

DEFAULT_CONFIG = {
    "max_pdf_size_mb": 50,
    "max_batch_size": 20,
    "session_timeout_minutes": 60,
    "cleanup_uploads_days": 7,
    "cleanup_outputs_days": 30,
    "cleanup_logs_days": 30,
}


def load_config() -> dict:
    if CONFIG_FILE.exists():
        try:
            data = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
            merged = dict(DEFAULT_CONFIG)
            merged.update({k: data[k] for k in data if k in DEFAULT_CONFIG})
            return merged
        except Exception:
            pass
    return dict(DEFAULT_CONFIG)


def save_config(config: dict):
    clean = dict(DEFAULT_CONFIG)
    for key in DEFAULT_CONFIG:
        if key in config:
            clean[key] = config[key]
    CONFIG_FILE.write_text(json.dumps(clean, indent=2), encoding="utf-8")
