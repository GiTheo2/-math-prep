#!/usr/bin/env python3
"""
Plan a focused math study session based on available time.
Usage: python3 session.py <minutes>
Example: python3 session.py 30
"""

import sys
import datetime
import anthropic

ARMY_START = datetime.date(2026, 6, 29)

PHASES = [
    (range(1,  9),  "Epsilon-Delta & Real Analysis Foundations",
     "Abbott Ch. 1–4: real number axioms, completeness, epsilon-N sequences, epsilon-delta limits and continuity"),
    (range(9,  17), "Linear Algebra (Abstract)",
     "Axler Ch. 1–3: vector space axioms, subspaces, span, linear independence, bases, dimension, linear maps, kernel, image, rank-nullity"),
    (range(17, 25), "Sequences, Series & Continuity (Rigorous)",
     "Abbott Ch. 2–3, 6: Cauchy sequences, Bolzano-Weierstrass, uniform continuity, series convergence tests"),
    (range(25, 33), "Derivatives & Integration (Rigorous)",
     "Abbott Ch. 5–7: MVT, Taylor with remainder, Riemann integral definition, Fundamental Theorem proof"),
    (range(33, 44), "Problem-Solving Sprint",
     "Past Unige Analysis I & Algèbre Linéaire I exam problems, timed practice, no notes"),
]

SYSTEM_PROMPT = """You are a focused mathematics study coach for a student in the Swiss army preparing for University of Geneva Mathematics.
Irregular schedule, limited sleep. Books: Abbott 'Understanding Analysis', Axler 'Linear Algebra Done Right'. Uses Supernote for handwritten exercises.

Given time and current phase, output a PRECISE, TIME-BOXED plan.
Rules:
- < 15 min: Anki reviews only, name the specific deck(s)
- 15–30 min: Anki (10 min) + one section to read OR one exercise
- 30–60 min: Anki (10 min) + read + 1–2 Supernote exercises
- 60–90 min: Anki + read + exercises + card generation suggestion
- 90+ min: Deep work — attempt a full proof from scratch

Format: [HH:MM–HH:MM] Activity  (start from 00:00)
End with one sentence: the single most important thing to internalize today."""

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 session.py <minutes>")
        sys.exit(1)
    try:
        minutes = int(sys.argv[1])
        assert 5 <= minutes <= 240
    except (ValueError, AssertionError):
        print("Error: minutes must be between 5 and 240")
        sys.exit(1)

    today = datetime.date.today()
    delta = (today - ARMY_START).days
    week = max(0, delta // 7 + 1) if delta >= 0 else 0

    phase_name, phase_detail = PHASES[0][1], PHASES[0][2]
    for week_range, name, detail in PHASES:
        if week in week_range:
            phase_name, phase_detail = name, detail
            break

    client = anthropic.Anthropic()
    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=800,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content":
            f"Date: {today.strftime('%A %d %B %Y')}\n"
            f"Army week: {week}/43\n"
            f"Phase: {phase_name}\n"
            f"Detail: {phase_detail}\n"
            f"Available: {minutes} minutes\n\n"
            "Give me the exact plan."
        }]
    )

    print(f"\nSession · {minutes} min · {phase_name}")
    print("─" * 52)
    print(message.content[0].text.strip())
    print()

if __name__ == '__main__':
    main()
