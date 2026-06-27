#!/usr/bin/env python3
"""
Reillum Daily Planner
Reads both inboxes, extracts tasks with Claude, creates Calendar events,
writes today.json, and pushes to GitHub.

Usage:
  python planner.py              # full run
  python planner.py --dry-run    # print output, no Calendar/git changes
  python planner.py --setup      # OAuth setup only (both accounts + calendar)
"""
import json, sys, subprocess
from datetime import datetime
from pathlib import Path

BASE = Path(__file__).parent


def push_to_github():
    try:
        subprocess.run(['git', '-C', str(BASE), 'add', 'today.json'], check=True)
        msg = f'Planner: {datetime.now().strftime("%Y-%m-%d %H:%M")}'
        subprocess.run(['git', '-C', str(BASE), 'commit', '-m', msg], check=True)
        subprocess.run(['git', '-C', str(BASE), 'push'], check=True)
        print('[git] Pushed today.json')
    except subprocess.CalledProcessError as e:
        print(f'[warn] Git push failed: {e}')


def setup_oauth():
    """Run OAuth flow for all three credential sets."""
    from gmail_reader import _get_service, SCOPES as GMAIL_SCOPES, CREDS_DIR
    from calendar_writer import _get_service as get_cal_service

    print('\n=== Setup: Personal Gmail (theodaude24@gmail.com) ===')
    _get_service(CREDS_DIR / 'personal_credentials.json', CREDS_DIR / 'personal_token.json')
    print('Personal Gmail OK')

    print('\n=== Setup: Professional Gmail (hello@reillum.com) ===')
    _get_service(CREDS_DIR / 'professional_credentials.json', CREDS_DIR / 'professional_token.json')
    print('Professional Gmail OK')

    print('\n=== Setup: Google Calendar ===')
    get_cal_service()
    print('Calendar OK\n')
    print('All OAuth tokens saved. You can now run: python planner.py')


def main(dry_run: bool = False):
    today_str = datetime.now().strftime('%Y-%m-%d')

    print(f'[planner] Starting — {today_str} (dry_run={dry_run})')

    from gmail_reader import read_emails
    emails = read_emails()
    print(f'[planner] {len(emails)} total emails')

    from ai_extractor import extract_tasks
    tasks = extract_tasks(emails)
    print(f'[planner] {len(tasks)} action items extracted')

    if not dry_run:
        from calendar_writer import create_events
        tasks = create_events(tasks)

    today_tasks = [t for t in tasks if t.get('due') == today_str]
    upcoming = sorted(
        [t for t in tasks if t.get('due') and t.get('due') > today_str],
        key=lambda t: t['due']
    )[:15]

    output = {
        'generated': datetime.now().isoformat(),
        'today': today_tasks,
        'upcoming': upcoming,
    }

    if dry_run:
        print('\n--- today.json preview ---')
        print(json.dumps(output, indent=2))
    else:
        (BASE / 'today.json').write_text(json.dumps(output, indent=2))
        print(f'[planner] today.json written ({len(today_tasks)} today, {len(upcoming)} upcoming)')
        push_to_github()

    print('[planner] Done.')


if __name__ == '__main__':
    if '--setup' in sys.argv:
        setup_oauth()
    else:
        main(dry_run='--dry-run' in sys.argv)
