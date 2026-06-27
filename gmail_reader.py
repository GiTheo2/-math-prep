#!/usr/bin/env python3
"""Read recent emails from both Gmail accounts."""
import time, base64
from datetime import datetime
from pathlib import Path
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

# gmail.modify = superset of readonly; also allows labeling + draft creation
SCOPES = ['https://www.googleapis.com/auth/gmail.modify']
CREDS_DIR = Path(__file__).parent / 'creds'


def _get_service(creds_file: Path, token_file: Path):
    creds = None
    if token_file.exists():
        creds = Credentials.from_authorized_user_file(str(token_file), SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(str(creds_file), SCOPES)
            creds = flow.run_local_server(port=0)
        token_file.write_text(creds.to_json())
    return build('gmail', 'v1', credentials=creds)


def _fetch_emails(service, hours: int) -> list:
    after_ts = int(time.time()) - hours * 3600
    result = service.users().messages().list(
        userId='me', q=f'after:{after_ts}', maxResults=50
    ).execute()

    emails = []
    for msg in result.get('messages', []):
        m = service.users().messages().get(
            userId='me', id=msg['id'],
            format='metadata',
            metadataHeaders=['From', 'Subject', 'Date']
        ).execute()
        headers = {h['name']: h['value'] for h in m.get('payload', {}).get('headers', [])}
        emails.append({
            'id': msg['id'],
            'thread_id': m.get('threadId', ''),
            'from': headers.get('From', ''),
            'subject': headers.get('Subject', ''),
            'snippet': m.get('snippet', ''),
            'date': headers.get('Date', ''),
        })
    return emails


def fetch_full_body(service, message_id: str, thread_id: str) -> dict:
    """Fetch full email body + last 3 thread messages for drafting context."""
    def _decode_part(part):
        data = part.get('body', {}).get('data', '')
        if data:
            return base64.urlsafe_b64decode(data).decode('utf-8', errors='replace')
        return ''

    def _extract_text(payload):
        mime = payload.get('mimeType', '')
        if mime == 'text/plain':
            return _decode_part(payload)
        if mime.startswith('multipart/'):
            for part in payload.get('parts', []):
                text = _extract_text(part)
                if text:
                    return text
        return ''

    # Full body of the target email
    msg = service.users().messages().get(
        userId='me', id=message_id, format='full'
    ).execute()
    body = _extract_text(msg.get('payload', {})) or msg.get('snippet', '')

    # Thread history (last 3 messages for context)
    thread = service.users().threads().get(
        userId='me', id=thread_id, format='metadata',
        metadataHeaders=['From', 'Subject', 'Date']
    ).execute()
    thread_msgs = thread.get('messages', [])[-3:]
    history = []
    for tm in thread_msgs:
        h = {hh['name']: hh['value'] for hh in tm.get('payload', {}).get('headers', [])}
        history.append(f"From: {h.get('From','')} | {h.get('Date','')}\n{tm.get('snippet','')}")

    return {'body': body[:3000], 'thread_history': history}


def get_services() -> dict:
    """Return {account_name: service} for both accounts."""
    creds_file = CREDS_DIR / 'credentials.json'
    if not creds_file.exists():
        print('[error] creds/credentials.json not found')
        return {}

    services = {}
    for token_name, account in [('personal_token.json', 'personal'), ('professional_token.json', 'professional')]:
        try:
            services[account] = _get_service(creds_file, CREDS_DIR / token_name)
        except Exception as e:
            print(f'[error] {account} service: {e}')
    return services


def read_emails() -> list:
    """Fetch last 24h emails from both accounts (48h on Mondays)."""
    hours = 48 if datetime.now().weekday() == 0 else 24
    all_emails = []
    services = get_services()

    for account, service in services.items():
        try:
            emails = _fetch_emails(service, hours)
            for e in emails:
                e['account'] = account
            all_emails.extend(emails)
            print(f'[{account}] {len(emails)} emails fetched')
        except Exception as ex:
            print(f'[error] {account}: {ex}')

    return all_emails
