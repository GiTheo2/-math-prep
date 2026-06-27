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
    creds_file = CREDS_DIR / 'personal_credentials.json'
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


def create_events(tasks: list) -> list:
    """Create Calendar events for tasks due within 7 days. Returns tasks unchanged."""
    if not tasks:
        return tasks

    try:
        service = _get_service()
    except Exception as e:
        print(f'[warn] Calendar skipped: {e}')
        return tasks

    today = datetime.now().strftime('%Y-%m-%d')
    cutoff = (datetime.now() + timedelta(days=7)).strftime('%Y-%m-%d')

    for task in tasks:
        due = task.get('due')
        if not due or due < today or due > cutoff:
            continue

        title = f"{task.get('action_verb', 'DO')}: {task['label']}"
        source_note = f"[{task.get('source', '')} inbox · auto-created by Reillum Planner]"
        body = {
            'summary': title,
            'description': f"{task.get('desc', '')}\n\n{source_note}",
            'start': {'date': due},
            'end': {'date': due},
            'colorId': '11' if task.get('priority') == 'high' else '5',
        }
        try:
            event = service.events().insert(calendarId='primary', body=body).execute()
            task['calendar_event_id'] = event.get('id')
            print(f'[calendar] Created: {title} on {due}')
        except Exception as e:
            print(f'[warn] Event creation failed for "{task["label"]}": {e}')

    return tasks
