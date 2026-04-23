def test_non_stable_branch_period_added(self):
        lines = ["Fixed #123 -- Added a feature\n"]
        result = process_commit_message(lines, "main")
        self.assertIs(result[0].rstrip("\n").endswith("."), True)