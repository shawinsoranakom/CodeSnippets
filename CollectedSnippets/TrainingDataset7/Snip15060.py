def test_adds_stable_prefix(self):
        lines = ["Fixed #123 -- Added a feature.\n"]
        result = process_commit_message(lines, "stable/5.2.x")
        self.assertEqual(result[0], "[5.2.x] Fixed #123 -- Added a feature.\n")