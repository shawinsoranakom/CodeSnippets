def test_empty_body_unchanged(self):
        lines = ["# This is a comment.\n"]
        result = process_commit_message(lines, "stable/5.2.x")
        self.assertEqual(result, lines)