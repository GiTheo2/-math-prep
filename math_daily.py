#!/usr/bin/env python3
"""
Generates today's 3 daily math tasks (Anki / Read / Exercises)
based on current army week. Pure logic — no external APIs.

Usage (standalone check):
  python3 math_daily.py
"""
from datetime import date

ARMY_START = date(2026, 6, 29)

# (week_start, week_end, deck, book, chapter, section_desc, exercise_topic)
SCHEDULE = [
    (1,  2,  "Mathematics::02 - Real Analysis",      "Abbott", "Ch. 1", "The Real Numbers",                    "completeness axiom and supremum proofs"),
    (3,  4,  "Mathematics::02 - Real Analysis",      "Abbott", "Ch. 2", "Sequences and Series",                "epsilon-N sequence convergence"),
    (5,  6,  "Mathematics::02 - Real Analysis",      "Abbott", "Ch. 3", "Basic Topology of ℝ",                "open sets, compactness, connectedness"),
    (7,  8,  "Mathematics::02 - Real Analysis",      "Abbott", "Ch. 4", "Functional Limits & Continuity",     "epsilon-delta continuity and uniform continuity"),
    (9,  10, "Mathematics::03 - Linear Algebra",     "Axler",  "Ch. 1", "Vector Spaces",                      "vector space axioms and subspaces"),
    (11, 12, "Mathematics::03 - Linear Algebra",     "Axler",  "Ch. 2", "Finite-Dimensional Vector Spaces",   "linear independence and bases"),
    (13, 16, "Mathematics::03 - Linear Algebra",     "Axler",  "Ch. 3", "Linear Maps",                        "null space, range, rank-nullity theorem"),
    (17, 20, "Mathematics::04 - Sequences & Series", "Abbott", "Ch. 2–3 (revisited)", "Cauchy sequences and topology proofs", "Cauchy sequences and uniform continuity proofs"),
    (21, 24, "Mathematics::04 - Sequences & Series", "Abbott", "Ch. 6", "Sequences and Series of Functions",  "uniform convergence and Weierstrass M-test"),
    (25, 28, "Mathematics::05 - Calculus (Rigorous)","Abbott", "Ch. 5", "The Derivative",                     "Mean Value Theorem and Taylor's theorem"),
    (29, 32, "Mathematics::05 - Calculus (Rigorous)","Abbott", "Ch. 7", "The Riemann Integral",               "Riemann integrability criterion and FTA"),
    (33, 43, "Mathematics",                          "Past exams", "Unige Analysis I + Algèbre Linéaire I", "past exam problems", "past Unige year-1 exam problems"),
]

PHASE_NAMES = [
    (1,  8,  "Phase 1 — Epsilon-Delta"),
    (9,  16, "Phase 2 — Linear Algebra"),
    (17, 24, "Phase 3 — Sequences & Series (deeper)"),
    (25, 32, "Phase 4 — Derivatives & Integration"),
    (33, 43, "Phase 5 — Problem-Solving Sprint"),
]


def current_week(today: date = None) -> int:
    d = today or date.today()
    if d < ARMY_START:
        return 0
    return min((d - ARMY_START).days // 7 + 1, 43)


def _phase_name(week: int) -> str:
    for start, end, name in PHASE_NAMES:
        if start <= week <= end:
            return name
    return "Phase 5 — Problem-Solving Sprint"


def _row(week: int) -> tuple:
    for row in SCHEDULE:
        if row[0] <= week <= row[1]:
            return row
    return SCHEDULE[-1]


def daily_tasks(today: date = None) -> list:
    today = today or date.today()
    today_str = today.isoformat()
    week = current_week(today)

    if week == 0:
        return []

    w_start, w_end, deck, book, chapter, section, ex_topic = _row(week)
    phase = _phase_name(week)
    week_in_phase = week - w_start + 1
    phase_len = w_end - w_start + 1
    deck_short = deck.replace("Mathematics::", "")

    return [
        {
            "label": f"Anki — {deck_short} · 10 new cards",
            "due": today_str,
            "source": "math",
            "priority": "high",
            "action_verb": "ANKI",
            "desc": (
                f"{phase} (Week {week}/43, week {week_in_phase}/{phase_len} of this block).\n"
                f"Open deck '{deck}'. Reviews first, then 10 new cards."
            ),
        },
        {
            "label": f"Read — {book} {chapter}",
            "due": today_str,
            "source": "math",
            "priority": "high",
            "action_verb": "READ",
            "desc": (
                f"{section}. 20–30 min — focus on definitions and proof structure, not speed. "
                f"Mark anything you cannot reconstruct from memory."
            ),
        },
        {
            "label": f"Exercises — {ex_topic}",
            "due": today_str,
            "source": "math",
            "priority": "normal",
            "action_verb": "EXERCISES",
            "desc": (
                f'python3 exercises.py "{ex_topic}" 2 3\n'
                f"Difficulty 2 (standard), 3 problems. Write proofs in full — no shortcuts."
            ),
        },
    ]


if __name__ == "__main__":
    import json
    tasks = daily_tasks()
    week = current_week()
    if not tasks:
        print("Pre-army (starts 2026-06-29). No math tasks yet.")
    else:
        print(f"Week {week} — {_phase_name(week)}\n")
        for t in tasks:
            print(f"[{t['action_verb']}] {t['label']}")
            print(f"  {t['desc']}")
            print()
