def test_backport_note_separated_by_blank_line(self):
        sha = "abc123def456"
        lines = ["Fixed #123 -- Added a feature.\n"]
        result = process_commit_message(lines, "stable/5.2.x", cherry_sha=sha)
        note_idx = next(i for i, l in enumerate(result) if f"Backport of {sha}" in l)
        self.assertEqual(result[note_idx - 1], "\n")