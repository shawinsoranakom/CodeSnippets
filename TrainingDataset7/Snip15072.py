def test_no_cherry_sha_no_backport_note(self):
        lines = ["Fixed #123 -- Added a feature.\n"]
        result = process_commit_message(lines, "stable/5.2.x", cherry_sha=None)
        self.assertNotIn("Backport of", "".join(result))