"""One Line, One Laugh — make.fun bounty entry.

Writes a single funny line to $OUTPUT_DIR/entry.txt (default: `output`,
relative to the current working directory). Stdlib only, no network.

Gate (RULES.txt): entry.txt must be UTF-8, 1-140 characters, a single
line, and not whitespace-only. The file is written with no trailing
newline, so its byte length equals the text's character length.
"""

import os
import sys
from pathlib import Path

FINAL_TEXT = (
    "My therapist said I should stop talking to my plants, "
    "so now I just nod at them and they seem fine with it."
)

MAX_CHARS = 140


def validate_text(text):
    """Return True iff `text` satisfies the entry gate.

    Rules: 1-140 characters (Unicode code points), exactly one line
    (no CR or LF anywhere), and not whitespace-only.
    """
    if not isinstance(text, str):
        return False
    if len(text) < 1 or len(text) > MAX_CHARS:
        return False
    if "\n" in text or "\r" in text:
        return False
    if not text.strip():
        return False
    try:
        text.encode("utf-8", errors="strict")
    except (UnicodeEncodeError, UnicodeDecodeError):
        return False
    return True


def write_entry(text, output_dir):
    """Validate `text` and write it (UTF-8, no trailing newline).

    Returns the path written. Raises ValueError without writing
    anything when `text` fails validation.
    """
    if not validate_text(text):
        raise ValueError("entry text fails the 1-140 char single-line gate")
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    entry_path = out_dir / "entry.txt"
    entry_path.write_text(text, encoding="utf-8", newline="")
    return entry_path


def main():
    output_dir = os.environ.get("OUTPUT_DIR", "output")
    try:
        entry_path = write_entry(FINAL_TEXT, output_dir)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    except OSError as exc:
        print(f"error: cannot write entry: {exc}", file=sys.stderr)
        return 1
    print(f"wrote {entry_path} ({len(FINAL_TEXT)} chars)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
