#!/usr/bin/env python3
"""Use Claude Code CLI to extract action items from email metadata."""
import json, re, subprocess
from datetime import datetime

CLAUDE_BIN = '/Users/theodaude/.local/bin/claude'


def _call_claude(prompt: str) -> str:
    result = subprocess.run(
        [CLAUDE_BIN, '-p', '--output-format', 'text'],
        input=prompt, capture_output=True, text=True, timeout=120
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

Review these emails and extract ONLY the ones that require a specific action or contain a deadline.

Include as action items:
- Any real person replying to outreach or contact form (even if it's a "not interested")
- Email delivery failures / bounces → action is to remove that email from the list
- Upwork / freelance platform job notifications that match AI/automation work
- Client or lead emails
- Payment, invoice, or deadline emails

Ignore: newsletters, promotional offers, Google/platform security alerts (unless suspicious), receipts for known services, and purely informational automated reports.

Return a JSON array. Each item must have exactly these fields:
{{
  "id": "e-<number>",
  "email_id": "<the message id from id= field>",
  "thread_id": "<the thread id from thread= field>",
  "type": "email",
  "priority": "high" or "medium",
  "label": "Short action verb + object, max 60 chars",
  "desc": "One sentence explaining what needs doing and why",
  "source": "personal" or "professional",
  "due": "YYYY-MM-DD or null if no specific deadline",
  "action_verb": "REPLY" | "SEND" | "CALL" | "REVIEW" | "SUBMIT" | "FOLLOW-UP" | "PAY" | "BOOK",
  "needs_draft": true or false
}}

Priority rules:
- high = client/lead email, today's deadline, explicit "please respond by", payment, urgent tone
- medium = deadline within 7 days, professional follow-up, anything time-sensitive but not critical

needs_draft = true only when: action_verb is REPLY or FOLLOW-UP AND the email is from a real person (not an automated system or notification service).

Emails:
{email_list}

Respond with ONLY the JSON array, nothing else. If no action items, return []."""

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
