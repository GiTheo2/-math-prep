#!/usr/bin/env python3
"""
Reillum Daily Planner
Reads both inboxes, extracts tasks with Claude Code CLI, flags important emails,
auto-drafts replies, creates Calendar events, writes today.json, pushes to GitHub.

Usage:
  python planner.py              # full run
  python planner.py --dry-run    # print output only, no Gmail/Calendar/git writes
  python planner.py --setup      # OAuth setup (run once after scope change)
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
    """Re-run OAuth with gmail.modify scope. Browser opens 3 times."""
    from gmail_reader import _get_service, CREDS_DIR
    from calendar_writer import _get_service as get_cal_service

    creds_file = CREDS_DIR / 'credentials.json'
    if not creds_file.exists():
        print(f'[error] {creds_file} not found.')
        return

    # Delete old tokens so we get fresh ones with the new scope
    for token in ['personal_token.json', 'professional_token.json']:
        t = CREDS_DIR / token
        if t.exists():
            t.unlink()
            print(f'[setup] Removed old {token}')

    print('\n=== Step 1/3: Personal Gmail ===')
    print('Browser will open → sign in as theodaude24@gmail.com')
    _get_service(creds_file, CREDS_DIR / 'personal_token.json')
    print('✓ Personal Gmail OK\n')

    print('=== Step 2/3: Professional Gmail ===')
    print('Browser will open → sign in as hello@reillum.com')
    _get_service(creds_file, CREDS_DIR / 'professional_token.json')
    print('✓ Professional Gmail OK\n')

    print('=== Step 3/3: Google Calendar ===')
    print('Browser will open → sign in as theodaude24@gmail.com')
    get_cal_service()
    print('✓ Calendar OK\n')
    print('All done. Run: python3 planner.py --dry-run')


def main(dry_run: bool = False):
    today_str = datetime.now().strftime('%Y-%m-%d')
    print(f'[planner] Starting — {today_str} (dry_run={dry_run})')

    # 1. Read emails
    from gmail_reader import read_emails, get_services
    emails = read_emails()
    seen_ids, unique_emails = set(), []
    for e in emails:
        if e['id'] not in seen_ids:
            seen_ids.add(e['id'])
            unique_emails.append(e)
    emails = unique_emails
    print(f'[planner] {len(emails)} total emails')

    # 2. Extract + deduplicate tasks
    from ai_extractor import extract_tasks
    tasks = [t for t in extract_tasks(emails) if isinstance(t, dict)]
    seen, unique_tasks = set(), []
    for t in tasks:
        key = (t.get('label', '').lower().strip(), t.get('due'), t.get('source'))
        if key not in seen:
            seen.add(key)
            unique_tasks.append(t)
    tasks = unique_tasks
    print(f'[planner] {len(tasks)} action items extracted')

    if not dry_run:
        services = get_services()

        # 3. Flag important emails in Gmail
        from email_flagger import flag_emails
        flag_emails(tasks, services)

        # 4. Auto-draft replies for REPLY/FOLLOW-UP tasks
        from email_drafter import draft_replies
        drafts = draft_replies(tasks, services)

        # 5. Create Calendar events
        from calendar_writer import create_events
        tasks = create_events(tasks)
    else:
        drafts = []
        needs_draft = [t for t in tasks if t.get('needs_draft')]
        if needs_draft:
            print(f'[dry-run] Would draft {len(needs_draft)} replies:')
            for t in needs_draft:
                print(f'  → {t["label"]}')

    # 6. Build and write today.json
    from math_daily import daily_tasks
    math_tasks = daily_tasks()

    # Items due today OR with no deadline (act on them today)
    today_tasks = math_tasks + [t for t in tasks if not t.get('due') or t.get('due') == today_str]
    upcoming = sorted(
        [t for t in tasks if t.get('due') and t.get('due') > today_str],
        key=lambda t: t['due']
    )[:15]

    output = {
        'generated': datetime.now().isoformat(),
        'today': today_tasks,
        'upcoming': upcoming,
        'drafts': drafts,
    }

    if dry_run:
        print('\n--- today.json preview ---')
        print(json.dumps(output, indent=2))
    else:
        (BASE / 'today.json').write_text(json.dumps(output, indent=2))
        print(f'[planner] today.json written ({len(today_tasks)} today, {len(upcoming)} upcoming, {len(drafts)} drafts)')
        push_to_github()

    print('[planner] Done.')


if __name__ == '__main__':
    if '--setup' in sys.argv:
        setup_oauth()
    else:
        main(dry_run='--dry-run' in sys.argv)
