#!/usr/bin/env python3
"""
Generate Anki flashcards and push directly to Anki via AnkiConnect.

CHAPTER MODE (recommended — no gaps):
  python3 cards.py --chapter abbott-1        # all concepts in Abbott Ch.1
  python3 cards.py --chapter axler-2         # all concepts in Axler Ch.2
  python3 cards.py --status                  # show coverage across all chapters

FREE-FORM MODE (targeted additions):
  python3 cards.py "epsilon-delta limits" 10
  python3 cards.py "vector spaces" 8 "Mathematics::03 - Linear Algebra"

Requires: Anki open with AnkiConnect addon (port 8765).
Falls back to CSV if Anki is not running.
"""

import sys
import os
import csv
import json
import datetime
import urllib.request
import anthropic

CURRICULUM_PATH = os.path.join(os.path.dirname(__file__), "curriculum.json")
DEFAULT_DECK = "Mathematics::02 - Real Analysis"
CARDS_PER_CONCEPT = 6

SYSTEM_PROMPT = """You are a mathematics professor creating Anki flashcards for a first-year university mathematics student.
Preparing for Analysis I and Algèbre Linéaire I at University of Geneva.
Level: Swiss Maturité 4.5/6. Proof vocabulary is decent; epsilon-delta and abstract linear algebra are weak points.

Rules:
- Every definition card must give the FORMAL definition, not an informal description
- Use LaTeX: $ for inline, $$ for display
- Cards must be atomic: one concept per card
- Vary types: definition, theorem statement, proof technique, "why is this needed", counterexample
- Answers must be complete and self-contained — no "see above"
- Do NOT generate trivial formula cards
- DO generate cards like: "State the ε-δ definition of continuity at a point" or "What are the THREE conditions to check that a subset is a subspace?"

Output: exactly N cards, one per line, format:
FRONT ||| BACK

No numbering. No other text."""


def anki_request(action, **params):
    payload = json.dumps({"action": action, "version": 6, "params": params}).encode()
    req = urllib.request.Request("http://localhost:8765", payload)
    with urllib.request.urlopen(req, timeout=3) as r:
        result = json.loads(r.read())
    if result.get("error"):
        raise Exception(result["error"])
    return result["result"]


def anki_available():
    try:
        anki_request("version")
        return True
    except:
        return False


def push_to_anki(cards, deck, tags):
    anki_request("createDeck", deck=deck)
    notes = [
        {
            "deckName": deck,
            "modelName": "Basic",
            "fields": {"Front": front, "Back": back},
            "options": {"allowDuplicate": False},
            "tags": tags,
        }
        for front, back in cards
    ]
    results = anki_request("addNotes", notes=notes)
    added = sum(1 for r in results if r is not None)
    return added, len(results) - added


def save_csv(cards, topic):
    os.makedirs(os.path.join(os.path.dirname(__file__), "output"), exist_ok=True)
    safe = topic.replace(" ", "_").replace("/", "-")[:40]
    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M")
    path = os.path.join(os.path.dirname(__file__), "output", f"cards_{safe}_{ts}.csv")
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f, delimiter=";", quoting=csv.QUOTE_ALL)
        writer.writerow(["Front", "Back"])
        for front, back in cards:
            writer.writerow([front, back])
    return path


def generate_cards(topic, n):
    client = anthropic.Anthropic()
    msg = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=4096,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content":
            f'Generate {n} Anki flashcards on: "{topic}"\n'
            f"Focus on definition-level and theorem-level cards for first-year university mathematics."
        }],
    )
    cards = []
    for line in msg.content[0].text.strip().splitlines():
        if " ||| " in line:
            front, back = line.split(" ||| ", 1)
            cards.append((front.strip(), back.strip()))
    return cards


def load_curriculum():
    with open(CURRICULUM_PATH, encoding="utf-8") as f:
        return json.load(f)


def save_curriculum(data):
    with open(CURRICULUM_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def cmd_status():
    data = load_curriculum()
    print(f"\n{'Chapter':<14} {'Title':<42} {'Done':>4} {'Total':>5} {'Bar'}")
    print("─" * 80)
    for ch in data["chapters"]:
        total = len(ch["concepts"])
        done = sum(1 for c in ch["concepts"] if c["status"] == "done")
        bar_len = 20
        filled = int(bar_len * done / total) if total else 0
        bar = "█" * filled + "░" * (bar_len - filled)
        print(f"{ch['id']:<14} {ch['title']:<42} {done:>4}/{total:<4} {bar}")
    total_all = sum(len(ch["concepts"]) for ch in data["chapters"])
    done_all = sum(
        sum(1 for c in ch["concepts"] if c["status"] == "done")
        for ch in data["chapters"]
    )
    print("─" * 80)
    print(f"{'TOTAL':<57} {done_all:>4}/{total_all:<4}\n")


def cmd_chapter(chapter_id):
    data = load_curriculum()
    chapter = next((ch for ch in data["chapters"] if ch["id"] == chapter_id), None)
    if not chapter:
        ids = [ch["id"] for ch in data["chapters"]]
        print(f"Chapter '{chapter_id}' not found. Available: {', '.join(ids)}")
        sys.exit(1)

    pending = [c for c in chapter["concepts"] if c["status"] == "pending"]
    if not pending:
        print(f"All concepts in {chapter_id} are already done. Use --status to check.")
        return

    use_anki = anki_available()
    if not use_anki:
        print("Warning: Anki not running — will save to CSV instead.\n")

    print(f"\nGenerating cards for: {chapter['title']} ({chapter_id})")
    print(f"  {len(pending)} concepts pending  ·  ~{len(pending) * CARDS_PER_CONCEPT} cards total")
    print(f"  Deck: {chapter['deck']}\n")

    total_added = 0
    for i, concept in enumerate(pending, 1):
        print(f"  [{i}/{len(pending)}] {concept['label'][:70]}")
        cards = generate_cards(concept["label"], CARDS_PER_CONCEPT)
        if not cards:
            print(f"    ⚠ No cards parsed — skipping")
            continue

        tags = ["math-prep", chapter_id, concept["id"]]
        if use_anki:
            added, dupes = push_to_anki(cards, chapter["deck"], tags)
            print(f"    → {added} added to Anki" + (f", {dupes} dupes" if dupes else ""))
            total_added += added
        else:
            path = save_csv(cards, f"{chapter_id}_{concept['id']}")
            print(f"    → CSV: {os.path.basename(path)}")

        concept["status"] = "done"
        save_curriculum(data)

    print(f"\nDone. {total_added} cards added to '{chapter['deck']}'." if use_anki else "\nDone. Import CSV files into Anki.")


def cmd_freeform(topic, n, deck):
    print(f"Generating {n} cards on: {topic} ...")
    cards = generate_cards(topic, n)
    if not cards:
        print("Error: no cards parsed.")
        sys.exit(1)
    print(f"Generated {len(cards)} cards.")

    if anki_available():
        added, dupes = push_to_anki(cards, deck, ["math-prep"])
        print(f"\nPushed to Anki: {deck}")
        print(f"  {added} added" + (f", {dupes} dupes skipped" if dupes else ""))
        print("\nPreview:")
        for front, back in cards[:3]:
            print(f"  Q: {front[:80]}")
            print(f"  A: {back[:100]}\n")
    else:
        path = save_csv(cards, topic)
        print(f"\nAnki not running — saved to: {path}")
        print("Import: Anki → File → Import → CSV, separator: semicolon")


def main():
    args = sys.argv[1:]

    if not args or args[0] == "--help":
        print(__doc__)
        return

    if args[0] == "--status":
        cmd_status()
        return

    if args[0] == "--chapter":
        if len(args) < 2:
            print("Usage: python3 cards.py --chapter <chapter-id>")
            print("Run --status to see chapter IDs.")
            sys.exit(1)
        cmd_chapter(args[1])
        return

    # Free-form mode
    if len(args) < 2:
        print("Usage: python3 cards.py <topic> <n> [deck]")
        sys.exit(1)
    topic = args[0]
    try:
        n = int(args[1])
        assert 1 <= n <= 50
    except (ValueError, AssertionError):
        print("Error: n must be between 1 and 50")
        sys.exit(1)
    deck = args[2] if len(args) > 2 else DEFAULT_DECK
    cmd_freeform(topic, n, deck)


if __name__ == "__main__":
    main()
