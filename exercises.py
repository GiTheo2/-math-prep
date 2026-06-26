#!/usr/bin/env python3
"""
Generate mathematics exercises with full solutions.
Usage: python3 exercises.py <topic> <difficulty> <n>
       difficulty: 1 (guided) | 2 (standard) | 3 (hard/Unige exam level)
Example: python3 exercises.py "epsilon-delta continuity" 2 5
"""

import sys
import os
import datetime
import anthropic

SYSTEM_PROMPT = """You are a mathematics professor setting problem sets for first-year university mathematics at University of Geneva.
Student level: Swiss Maturité 4.5/6. Working on epsilon-delta and abstract linear algebra.

Difficulty:
1 = Guided — broken into sub-steps
2 = Standard — student must find the proof path alone
3 = Hard — requires combining ideas, Unige exam difficulty

For each exercise, format exactly like this:

## Exercise N

**Problem:** [precise problem in LaTeX]

---

**Solution:**
[complete step-by-step solution, no "it is easy to see that"]

□

---

Generate exactly N exercises. No other text."""

LABELS = {1: 'Guided', 2: 'Standard', 3: 'Hard (Unige exam level)'}

def main():
    if len(sys.argv) < 4:
        print("Usage: python3 exercises.py <topic> <difficulty> <n>")
        print('Example: python3 exercises.py "epsilon-delta continuity" 2 5')
        sys.exit(1)

    topic = sys.argv[1]
    try:
        difficulty = int(sys.argv[2])
        assert difficulty in (1, 2, 3)
    except (ValueError, AssertionError):
        print("Error: difficulty must be 1, 2, or 3")
        sys.exit(1)
    try:
        n = int(sys.argv[3])
        assert 1 <= n <= 20
    except (ValueError, AssertionError):
        print("Error: n must be between 1 and 20")
        sys.exit(1)

    print(f"Generating {n} exercises on: {topic} (difficulty {difficulty}/3 — {LABELS[difficulty]}) ...")

    client = anthropic.Anthropic()
    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=8192,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": f'Topic: "{topic}"\nDifficulty: {difficulty}/3 — {LABELS[difficulty]}\nCount: {n}'}]
    )
    content = message.content[0].text.strip()

    safe = topic.replace(' ', '_').replace('/', '-')[:40]
    ts = datetime.datetime.now().strftime('%Y%m%d_%H%M')
    path = os.path.join(os.path.dirname(__file__), 'output', f'ex_{safe}_d{difficulty}_{ts}.md')

    header = f"# Exercises: {topic}\n**Difficulty:** {difficulty}/3 — {LABELS[difficulty]}  |  **Count:** {n}\n\nWork each problem on Supernote before reading the solution.\n\n---\n\n"
    with open(path, 'w', encoding='utf-8') as f:
        f.write(header + content)

    print(f"Done → output/{os.path.basename(path)}")
    print("Work them on Supernote before reading the solutions.")

if __name__ == '__main__':
    main()
