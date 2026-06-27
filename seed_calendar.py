#!/usr/bin/env python3
"""
One-time script: push all deadlines.json milestones to Google Calendar.
Safe to re-run — checks for existing events before creating.

Usage:
  python3 seed_calendar.py           # push to Calendar
  python3 seed_calendar.py --dry-run # print what would be created
"""
import json, sys
from pathlib import Path

BASE = Path(__file__).parent


def _existing_summaries(service) -> set:
    existing = set()
    page_token = None
    while True:
        resp = service.events().list(
            calendarId='primary',
            timeMin='2026-01-01T00:00:00Z',
            timeMax='2028-01-01T00:00:00Z',
            singleEvents=True,
            pageToken=page_token,
            maxResults=500,
        ).execute()
        for e in resp.get('items', []):
            existing.add(e.get('summary', ''))
        page_token = resp.get('nextPageToken')
        if not page_token:
            break
    return existing


def main(dry_run: bool = False):
    deadlines = json.loads((BASE / 'deadlines.json').read_text())['deadlines']

    if dry_run:
        print(f"Would create {len(deadlines)} calendar events:\n")
        for d in deadlines:
            print(f"  {d['due']}  📐 {d['label']}")
            print(f"           {d['desc'][:90]}")
        return

    from calendar_writer import _get_service
    service = _get_service()
    existing = _existing_summaries(service)
    print(f"[seed] {len(existing)} existing events checked\n")

    created, skipped = 0, 0
    for d in deadlines:
        title = f"📐 {d['label']}"
        if title in existing:
            print(f"[skip] {title}")
            skipped += 1
            continue

        body = {
            'summary': title,
            'description': d['desc'],
            'start': {'date': d['due']},
            'end': {'date': d['due']},
            'colorId': '10',  # green — distinct from email tasks (red=high, blue=normal)
        }
        service.events().insert(calendarId='primary', body=body).execute()
        print(f"[seed] Created: {title} on {d['due']}")
        created += 1

    print(f"\nDone. {created} created, {skipped} already existed.")


if __name__ == '__main__':
    main(dry_run='--dry-run' in sys.argv)
