"""Regression checks for preserving manually curated note collections."""

import hashlib
import importlib.util
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest


PROJECT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("sync_notes", PROJECT / "scripts/sync_notes.py")
SYNC = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(SYNC)


class NotesIndexTests(unittest.TestCase):
    def test_preserves_manual_content_and_is_repeatable(self):
        current = (
            "---\ntitle: Notes\n---\n\nMy introduction.\n\n"
            + SYNC.COLLECTIONS_START + "\nOld generated links.\n" + SYNC.COLLECTIONS_END
            + "\n\n- [MATH1972 Seminar Notes](math1972-seminar/index.qmd)\n"
        )
        entries = [("Appendix", "appendix/index.qmd")]
        result = SYNC.update_notes_index(current, entries)
        self.assertEqual(result.split(SYNC.COLLECTIONS_START)[0], current.split(SYNC.COLLECTIONS_START)[0])
        self.assertEqual(result.split(SYNC.COLLECTIONS_END)[1], current.split(SYNC.COLLECTIONS_END)[1])
        self.assertIn("- [Appendix](<appendix/index.qmd>)", result)
        self.assertNotIn("Old generated links", result)
        self.assertEqual(SYNC.update_notes_index(result, entries), result)

    def test_missing_duplicate_or_reversed_markers_fail(self):
        for text in ("A manually written index.",
                     SYNC.COLLECTIONS_START * 2 + SYNC.COLLECTIONS_END,
                     SYNC.COLLECTIONS_END + SYNC.COLLECTIONS_START):
            with self.subTest(text=text), self.assertRaises(ValueError):
                SYNC.update_notes_index(text, [])

    def test_new_index_gets_a_generated_block(self):
        result = SYNC.update_notes_index(None, [("Appendix", "appendix/index.qmd")])
        self.assertEqual(result.count(SYNC.COLLECTIONS_START), 1)
        self.assertEqual(result.count(SYNC.COLLECTIONS_END), 1)
        self.assertIn("- [Appendix](<appendix/index.qmd>)", result)

    def test_full_sync_preserves_seminar_and_source_scope(self):
        with tempfile.TemporaryDirectory(prefix="seminar-sync-test-") as temporary:
            base = Path(temporary)
            project, vault = base / "site", base / "vault"
            (project / "scripts").mkdir(parents=True)
            shutil.copy2(PROJECT / "scripts/sync_notes.py", project / "scripts/sync_notes.py")
            shutil.copy2(PROJECT / "publish-map.yml", project / "publish-map.yml")
            (project / "notes").mkdir()
            shutil.copy2(PROJECT / "notes/index.qmd", project / "notes/index.qmd")
            folders = [("Appendix", "notes/appendix"), ("Atomization", "notes/atomization"),
                       ("Usyd/MATH1964/MATH1964 Notes", "notes/math1964")]
            for number, (source_folder, destination) in enumerate(folders):
                source = vault / source_folder / f"Example{number}.md"
                source.parent.mkdir(parents=True)
                source.write_text("# Example\n\nA short source note.\n", encoding="utf-8")
                output = project / destination / f"Example{number}.qmd"
                output.parent.mkdir(parents=True)
                output.write_text("---\ntitle: Reviewed Example\n---\n\nReviewed copy.\n", encoding="utf-8")
            excluded = vault / "Usyd/MATH1972/MATH1972 Seminar/NotSelected.md"
            excluded.parent.mkdir(parents=True)
            excluded.write_text("This folder is outside the recurring selection.\n", encoding="utf-8")
            before_sources = {p: hashlib.sha256(p.read_bytes()).hexdigest() for p in vault.rglob("*.md")}
            manual_suffix = (project / "notes/index.qmd").read_text(encoding="utf-8").split(SYNC.COLLECTIONS_END)[1]
            for _ in range(2):
                completed = subprocess.run(
                    [sys.executable, str(project / "scripts/sync_notes.py"), "--vault", str(vault), "--sync"],
                    check=True, capture_output=True, text=True,
                )
                self.assertIn("Selected: 3 non-empty notes", completed.stdout)
                self.assertNotIn("NotSelected", completed.stdout)
                index = (project / "notes/index.qmd").read_text(encoding="utf-8")
                self.assertEqual(index.split(SYNC.COLLECTIONS_END)[1], manual_suffix)
                self.assertEqual(index.count("MATH1972 Seminar Notes"), 1)
                self.assertEqual(len(list((project / ".sync-pending").rglob("*.qmd"))), 3)
                self.assertFalse((project / "notes/math1972-seminar/NotSelected.qmd").exists())
            after_sources = {p: hashlib.sha256(p.read_bytes()).hexdigest() for p in vault.rglob("*.md")}
            self.assertEqual(before_sources, after_sources)


if __name__ == "__main__":
    unittest.main()
