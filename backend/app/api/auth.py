from urllib.parse import parse_qsl

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.security import require_valid_api_key
from app.db.database import get_session
from app.tools import gmail

router = APIRouter(prefix="/api/auth", tags=["auth"], dependencies=[Depends(require_valid_api_key)])


class GmailStartResponse(BaseModel):
    authorization_url: str
    redirect_uri: str


class GmailFinishRequest(BaseModel):
    code: str
    redirect_uri: str = "http://localhost:8766"


class GmailStatusResponse(BaseModel):
    connected: bool


def _extract_oauth_values(candidate_value: str) -> tuple[str, str]:
    if "code=" in candidate_value:
        query = dict(parse_qsl(candidate_value))
        return query.get("code", ""), query.get("state", "")
    return candidate_value, ""


@router.post("/gmail/start", response_model=GmailStartResponse)
async def start_gmail_connection() -> GmailStartResponse:
    try:
        authorization_url, _ = gmail.start_authorization()
        return GmailStartResponse(authorization_url=authorization_url, redirect_uri="http://localhost:8766")
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Gmail OAuth setup failed: {exc}")


@router.post("/gmail/finish", response_model=GmailStatusResponse)
async def finish_gmail_connection(request: GmailFinishRequest) -> GmailStatusResponse:
    code, state_value = _extract_oauth_values(request.code)
    if not code:
        raise HTTPException(status_code=400, detail="No authorization code found. Copy the code from the browser address bar.")
    try:
        gmail.exchange_authorization_code(code, state_value)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Could not exchange the authorization code: {exc}")
    return GmailStatusResponse(connected=True)


@router.get("/gmail/status", response_model=GmailStatusResponse)
async def gmail_connection_status() -> GmailStatusResponse:
    return GmailStatusResponse(connected=gmail.is_connected())


@router.post("/browser/login")
async def browser_login(platform: str) -> dict[str, str]:
    from app.tools.browser import login_interactive

    return {"status": await login_interactive(platform)}


@router.post("/browser/finish-login")
async def browser_finish_login() -> dict[str, str]:
    from app.tools.browser import finish_login

    return {"status": await finish_login()}


@router.get("/browser/state")
async def browser_state() -> dict[str, str]:
    from app.tools.browser import navigate_current_page

    return await navigate_current_page()