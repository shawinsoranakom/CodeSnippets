def test_git_comments_preserved_at_end(self):
        sha = "abc123def456"
        lines = [
            "Fixed #123 -- Added a feature.\n",
            "# Please enter the commit message.\n",
            "# Changes to be committed:\n",
        ]
        result = process_commit_message(lines, "stable/5.2.x", cherry_sha=sha)
        self.assertEqual(result[-2], "# Please enter the commit message.\n")
        self.assertEqual(result[-1], "# Changes to be committed:\n")