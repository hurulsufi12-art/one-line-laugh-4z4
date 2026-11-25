"""Tests for the One Line, One Laugh entry (stdlib unittest only).

Gate (from RULES.txt): /output/entry.txt must be UTF-8, 1-140 characters,
a single line, and not whitespace-only. main.py writes the final text
to $OUTPUT_DIR/entry.txt (default: `output`, relative to CWD).
"""

import ast
import hashlib
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ENTRY_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ENTRY_DIR))

FINAL_TEXT = (
    "My therapist said I should stop talking to my plants, "
    "so now I just nod at them and they seem fine with it."
)
ALLOWED_IMPORTS = {"os", "pathlib", "sys"}


def run_main(output_dir):
    """Run main.py as a subprocess with OUTPUT_DIR set; return CompletedProcess."""
    env = dict(os.environ)
    env["OUTPUT_DIR"] = str(output_dir)
    return subprocess.run(
        [sys.executable, "main.py"],
        cwd=str(ENTRY_DIR),
        env=env,
        capture_output=True,
        text=True,
        timeout=30,
    )


class TestEntryOutput(unittest.TestCase):
    def test_output_exists_and_is_utf8(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = run_main(tmp)
            self.assertEqual(result.returncode, 0, msg=result.stderr)
            entry = Path(tmp) / "entry.txt"
            self.assertTrue(entry.is_file(), "entry.txt was not created")
            # Strict UTF-8 decode; raises UnicodeDecodeError on bad bytes.
            entry.read_text(encoding="utf-8", errors="strict")

    def test_length_within_gate(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = run_main(tmp)
            self.assertEqual(result.returncode, 0, msg=result.stderr)
            content = (Path(tmp) / "entry.txt").read_text(encoding="utf-8")
            self.assertGreaterEqual(len(content), 1)
            self.assertLessEqual(len(content), 140)
            self.assertEqual(len(content), 107)

    def test_single_line(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = run_main(tmp)
            self.assertEqual(result.returncode, 0, msg=result.stderr)
            content = (Path(tmp) / "entry.txt").read_text(encoding="utf-8")
            self.assertNotIn("\n", content)
            self.assertNotIn("\r", content)
            # No trailing newline: file bytes are exactly the final text.
            self.assertEqual(content, FINAL_TEXT)

    def test_not_whitespace_only(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = run_main(tmp)
            self.assertEqual(result.returncode, 0, msg=result.stderr)
            content = (Path(tmp) / "entry.txt").read_text(encoding="utf-8")
            self.assertTrue(content.strip())

    def test_exact_final_text(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = run_main(tmp)
            self.assertEqual(result.returncode, 0, msg=result.stderr)
            raw = (Path(tmp) / "entry.txt").read_bytes()
            self.assertEqual(raw, FINAL_TEXT.encode("utf-8"))

    def test_output_path_via_env(self):
        # Relative OUTPUT_DIR is honoured, resolved against CWD.
        with tempfile.TemporaryDirectory() as tmp:
            env = dict(os.environ)
            env["OUTPUT_DIR"] = "out"
            result = subprocess.run(
                [sys.executable, "main.py"],
                cwd=tmp,
                env={**env, "PYTHONPATH": str(ENTRY_DIR)},
                capture_output=True,
                text=True,
                timeout=30,
            )
            # main.py lives in ENTRY_DIR; run it by path when CWD differs.
            if result.returncode != 0:
                result = subprocess.run(
                    [sys.executable, str(ENTRY_DIR / "main.py")],
                    cwd=tmp,
                    env=env,
                    capture_output=True,
                    text=True,
                    timeout=30,
                )
            self.assertEqual(result.returncode, 0, msg=result.stderr)
            self.assertTrue((Path(tmp) / "out" / "entry.txt").is_file())

    def test_deterministic(self):
        with tempfile.TemporaryDirectory() as tmp:
            first = run_main(Path(tmp) / "a")
            second = run_main(Path(tmp) / "b")
            self.assertEqual(first.returncode, 0, msg=first.stderr)
            self.assertEqual(second.returncode, 0, msg=second.stderr)
            hash_a = hashlib.sha256((Path(tmp) / "a" / "entry.txt").read_bytes()).hexdigest()
            hash_b = hashlib.sha256((Path(tmp) / "b" / "entry.txt").read_bytes()).hexdigest()
            self.assertEqual(hash_a, hash_b)


class TestValidation(unittest.TestCase):
    def test_empty_rejected(self):
        import main

        self.assertFalse(main.validate_text(""))

    def test_whitespace_only_rejected(self):
        import main

        self.assertFalse(main.validate_text("   \n\t"))
        self.assertFalse(main.validate_text("   "))

    def test_exactly_140_accepted(self):
        import main

        self.assertTrue(main.validate_text("x" * 140))

    def test_141_rejected(self):
        import main

        self.assertFalse(main.validate_text("x" * 141))

    def test_non_ascii_accepted(self):
        import main

        self.assertTrue(main.validate_text("café ☕"))

    def test_embedded_newline_rejected(self):
        import main

        self.assertFalse(main.validate_text("line one\nline two"))

    def test_rejects_crlf_and_embedded_newline(self):
        import main

        self.assertFalse(main.validate_text("line one\r\nline two"))
        self.assertFalse(main.validate_text("trailing newline\n"))
        self.assertFalse(main.validate_text("\nleading newline"))

    def test_invalid_not_written(self):
        import main

        with tempfile.TemporaryDirectory() as tmp:
            out_dir = Path(tmp) / "out"
            for bad in ("", "   ", "x" * 141, "a\nb"):
                with self.assertRaises(ValueError):
                    main.write_entry(bad, out_dir)
                self.assertFalse((out_dir / "entry.txt").exists())


class TestNoDeps(unittest.TestCase):
    def test_no_network_no_deps(self):
        tree = ast.parse((ENTRY_DIR / "main.py").read_text(encoding="utf-8"))
        imports = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports.update(alias.name.split(".")[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imports.add(node.module.split(".")[0])
        self.assertTrue(
            imports <= ALLOWED_IMPORTS,
            msg=f"non-stdlib/unauthorised imports: {sorted(imports - ALLOWED_IMPORTS)}",
        )


if __name__ == "__main__":
    unittest.main()
