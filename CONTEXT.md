# Math Prep — Context for Claude

Paste this into any new Claude conversation to immediately resume.

---

## Who I am

Theo, Geneva. Entering Mathematics at University of Geneva (Unige) in September 2027.
Swiss army: June 29 2026 → April 2027 (10 months). Post-army: May–Sept 2027 (5 months intensive).

Level: Swiss Maturité 4.5/6 in maths. Good: proof vocabulary, complex numbers, calculus formulas.
Weak: epsilon-delta analysis (formal), abstract linear algebra.

Goal: arrive at Unige already thinking like a mathematician — formal definitions, writing proofs from scratch.

---

## Books

- **Abbott "Understanding Analysis"** — primary text for analysis (owned)
- **Axler "Linear Algebra Done Right"** — primary text for linear algebra (to buy before Ch.1 of Axler)

---

## Study phases (army, 43 weeks)

| Phase | Weeks | Content |
|-------|-------|---------|
| Epsilon-Delta | 1–8 | Abbott Ch. 1–4 |
| Linear Algebra | 9–16 | Axler Ch. 1–3 |
| Sequences & Series | 17–24 | Abbott Ch. 2–3, 6 (deeper) |
| Derivatives & Integration | 25–32 | Abbott Ch. 5–7 |
| Problem-Solving Sprint | 33–43 | Past Unige exams, timed |

Army starts: 2026-06-29. To find current week: count weeks since that date.

---

## Infrastructure

All files live in `~/math-prep/`:

| File | Purpose |
|------|---------|
| `curriculum.json` | Complete chapter-by-chapter curriculum (Abbott Ch.1–7, Axler Ch.1–3). Each concept has a status: pending or done. The source of truth for what has been covered. |
| `cards.py` | Generates Anki cards via Claude API, pushes to Anki via AnkiConnect (port 8765). Chapter mode ensures no gaps. |
| `exercises.py` | Generates exercises with full solutions. Outputs Markdown to `output/`. |
| `session.py` | Given available minutes, outputs an exact time-boxed study plan for today's army week and phase. |
| `deadlines.json` | Deadlines shown on the dashboard. Edit this to add/update milestones. |
| `index.html` | Dashboard (deployed at https://githeo2.github.io/-math-prep). |

---

## Anki decks

- `Mathematics::02 - Real Analysis` — Abbott Ch. 1–4, 6
- `Mathematics::03 - Linear Algebra` — Axler Ch. 1–3
- `Mathematics::05 - Calculus (Rigorous)` — Abbott Ch. 5, 7
- `Mathematics::Foundations` — existing pre-army cards (keep, don't modify)
- `Mathematics::Foundations+` — existing pre-army cards (keep, don't modify)

---

## Key commands

```bash
cd ~/math-prep

# Check what's been covered
python3 cards.py --status

# Generate all cards for a chapter (chapter mode — no gaps)
python3 cards.py --chapter abbott-1
python3 cards.py --chapter abbott-2
python3 cards.py --chapter axler-1

# Generate targeted cards (free-form)
python3 cards.py "topic" 10
python3 cards.py "topic" 8 "Mathematics::03 - Linear Algebra"

# Generate exercises (difficulty 1=guided, 2=standard, 3=hard)
python3 exercises.py "epsilon-delta continuity" 2 5

# Plan a session
python3 session.py 30
```

---

## Dashboard deadlines

To add or update a deadline, edit `~/math-prep/deadlines.json` then:
```bash
cd ~/math-prep && git add deadlines.json && git commit -m "update deadlines" && git push
```
Dashboard updates in ~60 seconds.

---

## What to do next in a new conversation

1. Run `python3 cards.py --status` to see current coverage
2. Ask Claude: "Generate cards for the next pending chapter"
3. Or: "Generate 5 exercises on [topic] at difficulty 2"
4. Or: "Check this proof attempt: [paste proof]"

---

## Self-tests (phase-end, on Supernote, no notes)

| Phase end | Test |
|-----------|------|
| Week 8 | Prove ε-δ: lim_{x→2}(3x+1)=7. If f continuous and f(a)>0, prove ∃δ>0 s.t. f(x)>0 on (a−δ,a+δ). |
| Week 16 | State all 8 vector space axioms. Prove rank-nullity theorem. |
| Week 24 | Prove Bolzano-Weierstrass. Show ℚ is dense in ℝ. |
| Week 32 | State and prove the Fundamental Theorem of Analysis (both parts). |
| Week 43 | Complete a past Unige year-1 exam timed, blind, no notes. |
