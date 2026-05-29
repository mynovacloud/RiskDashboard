# PhillipCapital Risk Management — Automation Platform

A FastAPI web application for Risk Management automations. The first automation,
**Credit Worksheet**, reads customer PDFs (FOCUS-style filings), extracts helper-code
values, and produces completed Excel credit worksheets plus an audit report.

The codebase is structured so additional automations can be added without touching the
core infrastructure (auth, UI shell, jobs, downloads).

## Run

```bash
pip install -r requirements.txt
python -m uvicorn app:app --reload --host 0.0.0.0 --port 8000
```

`app.py` is the single entrypoint. It builds the FastAPI app via `create_app()`.

## Project structure

```
app.py                          Entrypoint — exposes `app` (uvicorn app:app)
pcrisk/
├── __init__.py                 Exposes create_app
├── factory.py                  create_app(): assembles app, mounts routers + automations
├── core/                       Shared infrastructure (automation-agnostic)
│   ├── paths.py                Directories, file names, constants
│   ├── config.py               App config load/save + defaults
│   ├── auth.py                 Password hashing, sessions, users, preset seeding
│   ├── jobs.py                 In-memory job/batch state, payloads, console text
│   ├── cleanup.py              Age-based output/log cleanup
│   └── templates.py            Backend Excel template detection + logo URL
├── ui/                         Shared presentation (byte-for-byte same GUI)
│   ├── styles.py               base_css()
│   ├── shell.py                head/topbar/hero/nav HTML builders
│   └── pages.py                Login, console, outputs, settings pages
├── routes/                     Shared (cross-automation) routes
│   ├── auth.py                 Login / logout
│   ├── pages.py                Console / outputs pages
│   ├── settings.py             Settings + user management
│   ├── api.py                  Shared JSON/status endpoints
│   └── downloads.py            Output / audit / zip downloads
└── automations/               One folder per automation
    ├── base.py                 Automation dataclass + registry (register/all/get/primary)
    └── credit_worksheet/       The first automation
        ├── automation.py       Registers this automation
        ├── routes.py           Its pages + processing endpoints (APIRouter)
        ├── pages.py            Its home/upload UI
        ├── engine.py           CreditWorksheetEngine (PDF -> Excel)
        ├── fields.py           FIELD_DEFINITIONS (helper code -> Excel cell)
        ├── audit.py            Audit report generation
        └── batch.py            Batch processing runner
```

## Adding a new automation

1. Create `pcrisk/automations/<your_automation>/`.
2. Build an `APIRouter` with its pages + endpoints in `routes.py`.
3. Add `automation.py` that calls `register(Automation(slug=..., name=..., router=...))`.
4. Import the package in `pcrisk/factory.py` (next to the credit_worksheet import).

The factory mounts every registered automation automatically. Set `is_primary=True`
on exactly one automation to own the root path (`/`).

## Legacy

`PDFtest.py` is the original Tkinter desktop version (V4) and is kept for reference. It is
standalone and not part of the web app.
