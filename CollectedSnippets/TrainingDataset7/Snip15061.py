def test_does_not_double_add_prefix(self):
        lines = ["[5.2.x] Fixed #123 -- Added a feature.\n"]
        result = process_commit_message(lines, "stable/5.2.x")
        self.assertEqual(result[0], "[5.2.x] Fixed #123 -- Added a feature.\n")