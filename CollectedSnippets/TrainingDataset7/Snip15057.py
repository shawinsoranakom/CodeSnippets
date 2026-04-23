def test_non_stable_branch_with_period_unchanged(self):
        lines = ["Fixed #123 -- Added a feature.\n"]
        result = process_commit_message(lines, "main")
        self.assertEqual(result, lines)