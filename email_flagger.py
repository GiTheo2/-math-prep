#!/usr/bin/env python3
"""Apply Gmail labels to important emails."""
from pathlib import Path


def _ensure_label(service, name: str) -> str:
    """Get or create a Gmail label by name, return its ID."""
    existing = service.users().labels().list(userId='me').execute().get('labels', [])
    for lbl in existing:
        if lbl['name'] == name:
            return lbl['id']
    created = service.users().labels().create(
        userId='me',
        body={'name': name, 'labelListVisibility': 'labelShow', 'messageListVisibility': 'show'}
    ).execute()
    return created['id']


def flag_emails(tasks: list, services: dict) -> None:
    """Apply Planner/High or Planner/Medium labels + star high-priority emails."""
    if not tasks or not services:
        return

    label_cache = {}

    for task in tasks:
        email_id = task.get('email_id')
        account = task.get('source')
        priority = task.get('priority')

        if not email_id or not account or account not in services:
            continue

        service = services[account]

        # Lazy-create labels per account
        key = f'{account}-{priority}'
        if key not in label_cache:
            label_name = f'Planner/{"High" if priority == "high" else "Medium"}'
            label_cache[key] = _ensure_label(service, label_name)

        add_labels = [label_cache[key]]
        if priority == 'high':
            add_labels.append('STARRED')

        try:
            service.users().messages().modify(
                userId='me', id=email_id,
                body={'addLabelIds': add_labels}
            ).execute()
            print(f'[flag] {priority.upper()} → {task["label"][:50]}')
        except Exception as e:
            print(f'[warn] Flag failed for {email_id}: {e}')
