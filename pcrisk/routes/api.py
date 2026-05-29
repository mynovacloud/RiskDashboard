from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import FileResponse

from pcrisk.core.auth import require_api_user
from pcrisk.core.jobs import get_job_payload
from pcrisk.core.paths import SHEET_NAME
from pcrisk.core.templates import get_logo_path, get_logo_url, get_template_status
from pcrisk.automations.credit_worksheet.fields import FIELD_DEFINITIONS

router = APIRouter()

@router.get("/favicon.ico")
def favicon():
    logo_path = get_logo_path()
    if not logo_path:
        raise HTTPException(status_code=404, detail="Favicon not found.")
    return FileResponse(path=str(logo_path), media_type="image/png", filename=logo_path.name)


@router.get("/health")
def health(request: Request):
    require_api_user(request)
    return {
        "status": "running",
        "template": get_template_status(),
        "logo_url": get_logo_url(),
        "field_count": len(FIELD_DEFINITIONS),
    }


@router.get("/api/status")
def api_status(request: Request):
    require_api_user(request)
    return {
        "status": "running",
        "template": get_template_status(),
        "field_count": len(FIELD_DEFINITIONS),
        "expected_sheet": SHEET_NAME,
    }


@router.get("/api/latest-result")
def api_latest_result(request: Request):
    require_api_user(request)
    return get_job_payload()


@router.get("/api/result/{job_id}")
def api_result(request: Request, job_id: str):
    require_api_user(request)
    return get_job_payload(job_id)
