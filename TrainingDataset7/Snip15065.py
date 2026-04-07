def test_adds_trailing_period(self):
        lines = ["Fixed #123 -- Added a feature\n"]
        result = process_commit_message(lines, "stable/5.2.x")
        self.assertIs(result[0].rstrip("\n").endswith("."), True)