def test_prefix_and_period_and_backport_combined(self):
        sha = "abc123def456"
        lines = ["Fixed #123 -- Added a feature\n"]
        result = process_commit_message(lines, "stable/5.2.x", cherry_sha=sha)
        self.assertEqual(result[0], "[5.2.x] Fixed #123 -- Added a feature.\n")
        self.assertIn(f"Backport of {sha} from main.\n", result)