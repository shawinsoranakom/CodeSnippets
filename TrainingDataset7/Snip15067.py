def test_adds_backport_note(self):
        sha = "abc123def456"
        lines = ["Fixed #123 -- Added a feature.\n"]
        result = process_commit_message(lines, "stable/5.2.x", cherry_sha=sha)
        self.assertIn(f"Backport of {sha} from main.\n", result)