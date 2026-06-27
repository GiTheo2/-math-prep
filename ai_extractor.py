#!/usr/bin/env python3
"""Use Claude to extract action items from email metadata."""
import json
from datetime import datetime
import anthropic

client = anthropic.Anthropic()


def extract_tasks(emails: list) -> list:
    if not emails:
        return []

    today = datetime.now().strftime('%Y-%m-%d')
    email_list = '\n\n'.join(
        f'[{i+1}] From: {e["from"]}\nSubject: {e["subject"]}\nSnippet: {e["snippet"]}\nAccount: {e["account"]}'
        for i, e in enumerate(emails)
    )

    prompt = f"""Today is {today}.

Review these emails and extract ONLY the ones that require a specific action or contain a deadline. Ignore newsletters, promotions, automated notifications, receipts, and purely informational emails.

Return a JSON array. Each item must have:
{{
  "id": "e-<number>",
  "type": "email",
  "priority": "high" or "medium",
  "label": "Short action verb + object, max 60 chars",
  "desc": "One sentence explaining what needs doing and why",
  "source": "personal" or "professional",
  "due": "YYYY-MM-DD or null if no specific deadline",
  "action_verb": "REPLY" | "SEND" | "CALL" | "REVIEW" | "SUBMIT" | "FOLLOW-UP" | "PAY" | "BOOK"
}}

Priority rules:
- high = client/lead email, today's deadline, explicit "please respond by", payment, urgent tone
- medium = deadline within 7 days, professional follow-up, anything time-sensitive but not critical

Emails:
{email_list}

Respond with ONLY the JSON array, nothing else. If no action items, return []."""

    try:
        response = client.messages.create(
            model='claude-haiku-4-5-20251001',
            max_tokens=1024,
            messages=[{'role': 'user', 'content': prompt}]
        )
        text = response.content[0].text.strip()
        start, end = text.find('['), text.rfind(']') + 1
        if start >= 0 and end > start:
            return json.loads(text[start:end])
        return []
    except Exception as e:
        print(f'[error] AI extraction: {e}')
        return []
