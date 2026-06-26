#!/usr/bin/env python3
"""
Generate Anki flashcards for university mathematics.
Usage: python3 cards.py <topic> <n>
Example: python3 cards.py "epsilon-delta limits" 10

Outputs a CSV file in output/ ready to import into Anki.
Anki import: File → Import → CSV, separator: semicolon, fields: Front;Back
"""

import sys
import os
import csv
import datetime
import anthropic

SYSTEM_PROMPT = """You are a mathematics professor creating Anki flashcards for a first-year university mathematics student.
The student is preparing for Analysis I (real analysis) and Linear Algebra I at University of Geneva.
Their level: completed Swiss Maturité with a 4.5/6 in maths. Good at proof vocabulary, weak at epsilon-delta and abstract linear algebra.

Rules for cards:
- Every definition card must state the FORMAL definition, not a colloquial one
- Use LaTeX for all mathematical notation (wrap in $ for inline, $$ for display)
- Question should test understanding or recall of a precise statement
- Answer should be complete and self-contained
- Cards should be atomic: one concept per card
- Vary card types: definition, theorem statement, proof technique, example, "why is this needed"
- Do NOT generate trivial formula cards (no "what is the derivative of sin x")
- DO generate cards like: "State the ε-δ definition of continuity at a point", "What does it mean for a sequence to be Cauchy?"

Output format: exactly N cards, one per line:
FRONT ||| BACK

Do not number the cards. Do not add any other text."""

def generate_cards(topic: str, n: int) -> list[tuple[str, str]]:
    client = anthropic.Anthropic()
    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=4096,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": f'Generate {n} Anki flashcards on the topic: "{topic}"\n\nFocus on definition-level and theorem-level cards for first-year university mathematics.'}]
    )
    raw = message.content[0].text.strip()
    cards = []
    for line in raw.splitlines():
        line = line.strip()
        if ' ||| ' in line:
            front, back = line.split(' ||| ', 1)
            cards.append((front.strip(), back.strip()))
    return cards

def main():
    if len(sys.argv) < 3:
        print("Usage: python3 cards.py <topic> <n>")
        print('Example: python3 cards.py "epsilon-delta limits" 10')
        sys.exit(1)

    topic = sys.argv[1]
    try:
        n = int(sys.argv[2])
        assert 1 <= n <= 50
    except (ValueError, AssertionError):
        print("Error: n must be between 1 and 50")
        sys.exit(1)

    print(f"Generating {n} cards on: {topic} ...")
    cards = generate_cards(topic, n)

    if not cards:
        print("Error: no cards parsed. Check API response.")
        sys.exit(1)

    safe = topic.replace(' ', '_').replace('/', '-')[:40]
    ts = datetime.datetime.now().strftime('%Y%m%d_%H%M')
    path = os.path.join(os.path.dirname(__file__), 'output', f'cards_{safe}_{ts}.csv')

    with open(path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f, delimiter=';', quoting=csv.QUOTE_ALL)
        writer.writerow(['Front', 'Back'])
        for front, back in cards:
            writer.writerow([front, back])

    print(f"\n{len(cards)} cards → output/{os.path.basename(path)}")
    print("\nPreview:")
    for front, back in cards[:3]:
        print(f"  Q: {front[:80]}")
        print(f"  A: {back[:100]}\n")
    print("Import: Anki → File → Import → CSV, separator: semicolon")

if __name__ == '__main__':
    main()
