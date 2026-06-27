#!/usr/bin/env python3
"""Create Google Calendar events for extracted tasks."""
from datetime import datetime, timedelta
from pathlib import Path
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

SCOPES = ['https://www.googleapis.com/auth/calendar']
CREDS_DIR = Path(__file__).parent / 'creds'


def _get_service():
    token_file = CREDS_DIR / 'calendar_token.json'
    creds_file = CREDS_DIR / 'credentials.json'
    if not creds_file.exists():
        raise FileNotFoundError(f'{creds_file} not found')

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

    return build('calendar', 'v3', credentials=creds)


GMAIL_ACCOUNTS = {
    'personal':     'theodaude24@gmail.com',
    'professional': 'hello@reillum.com',
}


def _gmail_link(task: dict) -> str:
    """Build a direct Gmail link to the email thread."""
    thread_id = task.get('thread_id') or task.get('email_id')
    if not thread_id:
        return ''
    account_email = GMAIL_ACCOUNTS.get(task.get('source', ''), '')
    if account_email:
        return f'https://mail.google.com/mail/u/{account_email}/#all/{thread_id}'
    return f'https://mail.google.com/mail/#all/{thread_id}'


def create_events(tasks: list) -> list:
    """Create Calendar events for all tasks. Null-due tasks are placed today."""
    if not tasks:
        return tasks

    try:
        service = _get_service()
    except Exception as e:
        print(f'[warn] Calendar skipped: {e}')
        return tasks

    today = datetime.now().strftime('%Y-%m-%d')
    cutoff = (datetime.now() + timedelta(days=14)).strftime('%Y-%m-%d')

    for task in tasks:
        # Null-due tasks go to today; skip tasks beyond 14 days
        due = task.get('due') or today
        if due > cutoff:
            continue

        title = f"{task.get('action_verb', 'DO')}: {task['label']}"
        gmail_url = _gmail_link(task)
        source_note = f"[{task.get('source', '')} inbox · auto-created by Reillum Planner]"
        description = task.get('desc', '')
        if gmail_url:
            description += f'\n\n📧 Open email: {gmail_url}'
        description += f'\n\n{source_note}'

        body = {
            'summary': title,
            'description': description,
            'start': {'date': due},
            'end': {'date': due},
            'colorId': '11' if task.get('priority') == 'high' else '5',
        }
        try:
            event = service.events().insert(calendarId='primary', body=body).execute()
            task['calendar_event_id'] = event.get('id')
            task['gmail_link'] = gmail_url
            print(f'[calendar] Created: {title} on {due}')
        except Exception as e:
            print(f'[warn] Event creation failed for "{task["label"]}": {e}')

    return tasks
