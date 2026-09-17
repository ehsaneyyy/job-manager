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


@router.post("/gmail/start", response_model=GmailStartResponse)
async def start_gmail_connection() -> GmailStartResponse:
    try:
        authorization_url, _ = gmail.build_auth_url()
        return GmailStartResponse(authorization_url=authorization_url, redirect_uri="http://localhost:8766")
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Gmail OAuth setup failed: {exc}")


@router.post("/gmail/finish", response_model=GmailStatusResponse)
async def finish_gmail_connection(request: GmailFinishRequest) -> GmailStatusResponse:
    _, flow = gmail.build_auth_url(request.redirect_uri)
    try:
        gmail.store_credentials_from_code(request.code, flow, request.redirect_uri)
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