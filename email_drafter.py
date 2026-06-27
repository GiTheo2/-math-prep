#!/usr/bin/env python3
"""Auto-draft Gmail replies using Claude Code CLI."""
import json, subprocess, base64, email as email_lib
from pathlib import Path

CLAUDE_BIN = '/Users/theodaude/.local/bin/claude'
CONTEXT_FILE = Path(__file__).parent / 'business_context.md'


def _call_claude(prompt: str) -> str:
    result = subprocess.run(
        [CLAUDE_BIN, '-p', prompt],
        capture_output=True, text=True, timeout=90
    )
    return result.stdout.strip()


def _load_context() -> str:
    if CONTEXT_FILE.exists():
        return CONTEXT_FILE.read_text()
    return '(No business context file found. Create business_context.md in the math-prep folder.)'


def _build_raw_reply(to: str, subject: str, body: str, thread_id: str) -> str:
    """Build a RFC 2822 message encoded as base64url."""
    subj = subject if subject.lower().startswith('re:') else f'Re: {subject}'
    msg = email_lib.message.EmailMessage()
    msg['To'] = to
    msg['Subject'] = subj
    msg.set_content(body)
    raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()
    return raw


def draft_replies(tasks: list, services: dict) -> list:
    """Create Gmail draft replies for tasks with needs_draft=True. Returns draft summaries."""
    context = _load_context()
    drafts = []

    for task in tasks:
        if not task.get('needs_draft'):
            continue

        email_id = task.get('email_id')
        thread_id = task.get('thread_id')
        account = task.get('source')

        if not email_id or not account or account not in services:
            continue

        service = services[account]

        # Fetch full body + thread history
        try:
            from gmail_reader import fetch_full_body
            content = fetch_full_body(service, email_id, thread_id)
        except Exception as e:
            print(f'[warn] Could not fetch body for {email_id}: {e}')
            continue

        thread_ctx = '\n---\n'.join(content['thread_history'])
        email_body = content['body']

        prompt = f"""You are drafting a reply on behalf of Theo (Reillum). Here is his business context:

{context}

---
Email thread history (oldest first):
{thread_ctx}

---
Email to reply to:
{email_body}

---
Write a reply email body only (no subject line, no "To:" header). Keep it under 120 words. Match Theo's tone from the context above. Be direct, warm, and professional. Do not use generic filler phrases like "I hope this email finds you well." End with a clear next step or call to action."""

        try:
            reply_body = _call_claude(prompt)
            if not reply_body:
                continue

            # Get sender address to reply to
            msg_meta = service.users().messages().get(
                userId='me', id=email_id, format='metadata',
                metadataHeaders=['From', 'Subject']
            ).execute()
            headers = {h['name']: h['value'] for h in msg_meta.get('payload', {}).get('headers', [])}
            to_addr = headers.get('From', '')
            subject = headers.get('Subject', '')

            raw = _build_raw_reply(to_addr, subject, reply_body, thread_id)
            draft = service.users().drafts().create(
                userId='me',
                body={'message': {'raw': raw, 'threadId': thread_id}}
            ).execute()

            draft_id = draft.get('id')
            print(f'[draft] Created for: {task["label"][:50]}')
            drafts.append({
                'task_label': task['label'],
                'draft_id': draft_id,
                'preview': reply_body[:120] + ('…' if len(reply_body) > 120 else ''),
                'account': account,
            })
        except Exception as e:
            print(f'[warn] Draft failed for "{task.get("label","?")}": {e}')

    return drafts
