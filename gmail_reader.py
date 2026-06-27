#!/usr/bin/env python3
"""Read recent emails from both Gmail accounts."""
import time
from datetime import datetime
from pathlib import Path
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']
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
            'from': headers.get('From', ''),
            'subject': headers.get('Subject', ''),
            'snippet': m.get('snippet', ''),
            'date': headers.get('Date', ''),
        })
    return emails


def read_emails() -> list:
    """Fetch last 24h emails from both accounts (48h on Mondays)."""
    hours = 48 if datetime.now().weekday() == 0 else 24
    all_emails = []

    accounts = [
        ('personal_credentials.json',     'personal_token.json',     'personal'),
        ('professional_credentials.json',  'professional_token.json', 'professional'),
    ]

    for creds_name, token_name, account in accounts:
        creds_file = CREDS_DIR / creds_name
        if not creds_file.exists():
            print(f'[warn] {creds_name} not found — skipping {account} account')
            continue
        try:
            service = _get_service(creds_file, CREDS_DIR / token_name)
            emails = _fetch_emails(service, hours)
            for e in emails:
                e['account'] = account
            all_emails.extend(emails)
            print(f'[{account}] {len(emails)} emails fetched')
        except Exception as ex:
            print(f'[error] {account}: {ex}')

    return all_emails
