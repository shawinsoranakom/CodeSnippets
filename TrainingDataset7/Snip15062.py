def test_summary_leading_whitespace_no_double_space_before_prefix(self):
        lines = ["  fixed #123 -- Added a feature.\n"]
        result = process_commit_message(lines, "stable/5.2.x")
        self.assertEqual(result[0], "[5.2.x] Fixed #123 -- Added a feature.\n")