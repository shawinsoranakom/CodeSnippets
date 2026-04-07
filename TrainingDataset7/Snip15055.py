def test_non_stable_branch_no_prefix_added(self):
        lines = ["Fixed #123 -- Added a feature.\n"]
        result = process_commit_message(lines, "main")
        self.assertNotIn("[", result[0].split("--")[0])