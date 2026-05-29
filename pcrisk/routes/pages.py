from typing import Optional

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, RedirectResponse

from pcrisk.core.auth import current_user_or_none
from pcrisk.ui.pages import (
    console_page_html,
    outputs_page_html,
    settings_page_html,
)

router = APIRouter()

@router.get("/console", response_class=HTMLResponse)
def console(request: Request, job_id: Optional[str] = None):
    user = current_user_or_none(request)
    if not user:
        return RedirectResponse("/login", status_code=303)
    return HTMLResponse(console_page_html(user, job_id))


@router.get("/outputs", response_class=HTMLResponse)
def outputs(request: Request):
    user = current_user_or_none(request)
    if not user:
        return RedirectResponse("/login", status_code=303)
    return HTMLResponse(outputs_page_html(user))


@router.get("/settings", response_class=HTMLResponse)
def settings_page(request: Request, msg: Optional[str] = None, t: Optional[str] = None):
    user = current_user_or_none(request)
    if not user:
        return RedirectResponse("/login", status_code=303)
    return HTMLResponse(settings_page_html(user, flash=msg or "", flash_type=t or "ok"))
