def test_does_not_double_add_backport_note(self):
        sha = "abc123def456"
        lines = [
            "Fixed #123 -- Added a feature.\n",
            "\n",
            f"Backport of {sha} from main.\n",
        ]
        result = process_commit_message(lines, "stable/5.2.x", cherry_sha=sha)
        self.assertEqual(len([line for line in result if "Backport" in line]), 1)