# Purpose:
# Inputs:
# Outputs:
# Dependencies:
# Notes:

from __future__ import annotations

import json
from pathlib import Path

from google.auth.transport.requests import Request
from google.auth.exceptions import RefreshError
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow

from common import require_env_var
from renderers import render_google_doc_entry
from schemas import SessionPayload


GOOGLE_DOCS_SCOPE = "https://www.googleapis.com/auth/documents"


def _load_client_config(oauth_client_path: Path) -> dict:
    with oauth_client_path.open("r", encoding="utf-8") as oauth_client_file:
        client_config = json.load(oauth_client_file)

    if "installed" not in client_config:
        available_types = ", ".join(sorted(client_config.keys()))
        raise RuntimeError(
            "GOOGLE_OAUTH_CLIENT_FILE must be a Desktop app OAuth client JSON for InstalledAppFlow. "
            f"Found client type(s): {available_types}. Create a Desktop app OAuth client in Google Cloud "
            "and replace the JSON file."
        )
    return client_config


def _run_desktop_oauth_flow(client_config: dict, oauth_token_path: Path) -> Credentials:
    flow = InstalledAppFlow.from_client_config(client_config, [GOOGLE_DOCS_SCOPE])
    credentials = flow.run_local_server(host="127.0.0.1", port=0)
    oauth_token_path.write_text(credentials.to_json(), encoding="utf-8")
    return credentials


def _load_or_create_credentials() -> Credentials:
    oauth_client_path = Path(require_env_var("GOOGLE_OAUTH_CLIENT_FILE"))
    oauth_token_path = Path(require_env_var("GOOGLE_OAUTH_TOKEN_FILE"))
    client_config = _load_client_config(oauth_client_path)

    credentials: Credentials | None = None
    if oauth_token_path.exists():
        credentials = Credentials.from_authorized_user_file(str(oauth_token_path), [GOOGLE_DOCS_SCOPE])

    if credentials and credentials.expired and credentials.refresh_token:
        try:
            credentials.refresh(Request())
            oauth_token_path.write_text(credentials.to_json(), encoding="utf-8")
        except RefreshError:
            oauth_token_path.unlink(missing_ok=True)
            credentials = _run_desktop_oauth_flow(client_config, oauth_token_path)
    elif not credentials or not credentials.valid:
        credentials = _run_desktop_oauth_flow(client_config, oauth_token_path)

    return credentials


def _build_docs_service():
    credentials = _load_or_create_credentials()
    return build("docs", "v1", credentials=credentials, cache_discovery=False)


def append_to_google_doc(document_id: str, payload: SessionPayload) -> None:
    if not document_id:
        raise RuntimeError(f"Missing Google Doc ID for business: {payload.business}")

    docs_service = _build_docs_service()
    rendered_entry = render_google_doc_entry(payload)
    docs_service.documents().batchUpdate(
        documentId=document_id,
        body={
            "requests": [
                {
                    "insertText": {
                        "endOfSegmentLocation": {},
                        "text": rendered_entry,
                    }
                }
            ]
        },
    ).execute()
