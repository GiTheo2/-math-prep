#!/usr/bin/env python3
"""Use Claude Code CLI to extract action items from email metadata."""
import json, os, re, subprocess
from datetime import datetime

CLAUDE_BIN = '/Users/theodaude/.local/bin/claude'

# Strip API key so claude CLI uses Claude Code subscription, not paid API credits
_ENV = {k: v for k, v in os.environ.items() if k != 'ANTHROPIC_API_KEY'}


def _call_claude(prompt: str) -> str:
    result = subprocess.run(
        [CLAUDE_BIN, '-p', '--output-format', 'text'],
        input=prompt, capture_output=True, text=True, timeout=120,
        env=_ENV
    )
    return result.stdout.strip()


def extract_tasks(emails: list) -> list:
    if not emails:
        return []

    today = datetime.now().strftime('%Y-%m-%d')
    email_list = '\n\n'.join(
        f'[{i+1}] id={e["id"]} thread={e.get("thread_id", "")} '
        f'From: {e["from"]}\nSubject: {e["subject"]}\nSnippet: {e["snippet"]}\nAccount: {e["account"]}'
        for i, e in enumerate(emails)
    )

    prompt = f"""Today is {today}.

Your job is simple: find emails from REAL HUMANS writing directly to Theo. That is the only thing that matters.

EXTRACT only:
- A real person replying to Theo's cold outreach (even "not interested" counts)
- A real person who filled out the contact form on reillum.com
- A real client or lead asking a question or following up
- A real person requesting a call, proposal, or collaboration

IGNORE everything else — no exceptions:
- Upwork job alerts, LinkedIn notifications, job board emails
- Delivery failures, bounce notifications
- Newsletters, promotions, marketing
- Google / platform security alerts
- Any automated system email (no-reply, noreply, mailer-daemon, notifications@, alerts@, etc.)

If the sender is a platform or automated system rather than a human being writing personally to Theo, ignore it.

Return a JSON array. Each item:
{{
  "id": "e-<number>",
  "email_id": "<message id from id= field>",
  "thread_id": "<thread id from thread= field>",
  "type": "email",
  "priority": "high",
  "label": "REPLY to [name] — [one phrase about topic]",
  "desc": "One sentence: who they are and what they want",
  "source": "personal" or "professional",
  "due": "{today}",
  "action_verb": "REPLY",
  "needs_draft": true
}}

All real-person emails are high priority and due today. Theo has a 1-day max rule for responding to anyone who writes to him directly.

Emails:
{email_list}

Respond with ONLY the JSON array, nothing else. If no real-person emails found, return []."""

    try:
        text = _call_claude(prompt)
        # Strip markdown code fences and single backtick wrapping
        text = re.sub(r'```(?:json)?\s*', '', text)
        text = re.sub(r'`(\[.*?\])`', r'\1', text, flags=re.DOTALL)
        text = text.strip()
        start = text.find('[')
        if start < 0:
            return []
        # Use raw_decode to stop at natural end of JSON array (ignores trailing text)
        result, _ = json.JSONDecoder().raw_decode(text, start)
        return result if isinstance(result, list) else []
    except Exception as e:
        print(f'[error] AI extraction: {e}')
        return []
