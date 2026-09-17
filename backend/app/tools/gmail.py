import base64
import json
import threading
from email.mime.text import MIMEText
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import parse_qsl, urlparse

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

from app.core.config import settings
from app.core.security import vault

SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.send",
    "https://www.googleapis.com/auth/gmail.modify",
]

_pending_flows: dict[str, InstalledAppFlow] = {}
_callback_server: ThreadingHTTPServer | None = None
_callback_server_lock = threading.Lock()


def load_gmail_oauth_client_config() -> dict[str, str]:
    backend_root = Path(__file__).resolve().parents[2]
    credentials_file = backend_root / "credentials.json"
    if credentials_file.exists():
        raw = json.loads(credentials_file.read_text(encoding="utf-8"))
        client_section = raw.get("installed") or raw.get("web") or {}
        return {
            "client_id": client_section["client_id"],
            "client_secret": client_section["client_secret"],
        }
    if settings.google_client_id and settings.google_client_secret:
        return {
            "client_id": settings.google_client_id,
            "client_secret": settings.google_client_secret,
        }
    raise RuntimeError(
        "Gmail is not set up yet. Do the one-time Google Cloud steps in SETUP.md (step 3), "
        "save the downloaded file as backend\\credentials.json, restart run.bat, then try again."
    )


def _build_flow(redirect_uri: str) -> InstalledAppFlow:
    client_config = load_gmail_oauth_client_config()
    return InstalledAppFlow.from_client_config(
        client_config={
            "installed": {
                "client_id": client_config["client_id"],
                "client_secret": client_config["client_secret"],
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "redirect_uris": [redirect_uri],
            }
        },
        scopes=SCOPES,
    )


def _extract_query_parameter(authorization_url: str, param_name: str) -> str:
    query_string = urlparse(authorization_url).query
    for key, value in parse_qsl(query_string):
        if key == param_name:
            return value
    return ""


def start_authorization(redirect_uri: str = "http://localhost:8766") -> tuple[str, str]:
    flow = _build_flow(redirect_uri)
    flow.redirect_uri = redirect_uri
    authorization_url, _ = flow.authorization_url(prompt="consent")
    state_value = _extract_query_parameter(authorization_url, "state")
    _pending_flows[state_value] = flow
    _ensure_callback_server(redirect_uri)
    return authorization_url, state_value


def exchange_authorization_code(code: str, state_value: str) -> None:
    flow = _pending_flows.pop(state_value, None)
    if flow is None:
        raise RuntimeError("Authorization flow not found or expired. Please start the connection again.")
    flow.fetch_token(code=code)
    _persist_credentials(flow.credentials)


def _persist_credentials(creds: Credentials) -> None:
    token_data = {
        "token": creds.token,
        "refresh_token": creds.refresh_token,
        "token_uri": creds.token_uri,
        "client_id": creds.client_id,
        "client_secret": creds.client_secret,
        "scopes": creds.scopes,
    }
    vault.store("gmail_token_json", json.dumps(token_data))


class _OAuthCallbackHandler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        query = dict(parse_qsl(urlparse(self.path).query))
        code = query.get("code", "")
        state_value = query.get("state", "")
        if not code or not state_value:
            self._respond(400, "<h2>Missing authorization code.</h2><p>Go back to JobBot and start again.</p>")
            return
        try:
            exchange_authorization_code(code, state_value)
            self._respond(200, "<h2>JobBot connected to your Gmail.</h2><p>You can close this tab and return to JobBot.</p>")
        except Exception:
            self._respond(400, "<h2>Could not connect.</h2><p>Go back to JobBot and try again.</p>")

    def _respond(self, status: int, body: str) -> None:
        encoded_body = body.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(encoded_body)))
        self.end_headers()
        self.wfile.write(encoded_body)

    def log_message(self, message_format: str, *args: Any) -> None:
        pass


def _ensure_callback_server(redirect_uri: str) -> None:
    global _callback_server
    with _callback_server_lock:
        if _callback_server is not None:
            return
        callback_port = int(urlparse(redirect_uri).port or 8766)
        _callback_server = ThreadingHTTPServer(("127.0.0.1", callback_port), _OAuthCallbackHandler)
        callback_thread = threading.Thread(target=_callback_server.serve_forever, daemon=True)
        callback_thread.start()


def _get_gmail_service() -> Any:
    token_json = vault.retrieve("gmail_token_json")
    if not token_json:
        raise RuntimeError(
            "Gmail is not connected. Start the connection at POST /api/auth/gmail/start"
        )
    import json

    token_data = json.loads(token_json)
    creds = Credentials(
        token=token_data["token"],
        refresh_token=token_data.get("refresh_token"),
        token_uri=token_data.get("token_uri", "https://oauth2.googleapis.com/token"),
        client_id=token_data.get("client_id"),
        client_secret=token_data.get("client_secret"),
        scopes=token_data.get("scopes", SCOPES),
    )
    if creds.expired and creds.refresh_token:
        creds.refresh(Request())
        token_data["token"] = creds.token
        vault.store("gmail_token_json", json.dumps(token_data))
    return build("gmail", "v1", credentials=creds)


def list_messages(query: str = "is:unread", max_results: int = 20) -> list[dict[str, str]]:
    service = _get_gmail_service()
    response = service.users().messages().list(userId="me", q=query, maxResults=max_results).execute()
    messages = response.get("messages", [])
    results = []
    for msg_meta in messages:
        full_msg = service.users().messages().get(userId="me", id=msg_meta["id"], format="full").execute()
        headers = {h["name"].lower(): h["value"] for h in full_msg.get("payload", {}).get("headers", [])}
        results.append(
            {
                "id": full_msg["id"],
                "thread_id": full_msg.get("threadId", ""),
                "subject": headers.get("subject", ""),
                "from": headers.get("from", ""),
                "snippet": full_msg.get("snippet", ""),
                "is_read": "UNREAD" not in full_msg.get("labelIds", []),
                "labels": full_msg.get("labelIds", []),
            }
        )
    return results


def get_thread(thread_id: str) -> list[dict[str, str]]:
    service = _get_gmail_service()
    thread = service.users().threads().get(userId="me", id=thread_id, format="full").execute()
    messages = []
    for msg in thread.get("messages", []):
        headers = {h["name"].lower(): h["value"] for h in msg.get("payload", {}).get("headers", [])}
        body = ""
        payload = msg.get("payload", {})
        if "data" in payload.get("body", {}):
            body = base64.urlsafe_b64decode(payload["body"]["data"]).decode("utf-8", errors="replace")
        elif payload.get("mimeType", "").startswith("text/plain"):
            for part in payload.get("parts", []):
                if part.get("mimeType") == "text/plain" and "data" in part.get("body", {}):
                    body = base64.urlsafe_b64decode(part["body"]["data"]).decode("utf-8", errors="replace")
                    break
        messages.append(
            {
                "id": msg["id"],
                "from": headers.get("from", ""),
                "to": headers.get("to", ""),
                "subject": headers.get("subject", ""),
                "date": headers.get("date", ""),
                "body": body,
            }
        )
    return messages


def send_email(to: str, subject: str, body: str, thread_id: str | None = None) -> str:
    service = _get_gmail_service()
    message = MIMEText(body)
    message["to"] = to
    message["subject"] = subject
    raw = base64.urlsafe_b64encode(message.as_bytes()).decode("ascii")
    params: dict[str, Any] = {"userId": "me", "body": {"raw": raw}}
    if thread_id:
        params["threadId"] = thread_id
    result = service.users().messages().send(**params).execute()
    return result["id"]


def mark_message_as_read(message_id: str) -> None:
    service = _get_gmail_service()
    service.users().messages().modify(userId="me", id=message_id, body={"removeLabelIds": ["UNREAD"]}).execute()


def is_connected() -> bool:
    return vault.retrieve("gmail_token_json") is not None