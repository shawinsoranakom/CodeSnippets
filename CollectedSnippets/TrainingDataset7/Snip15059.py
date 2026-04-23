def test_only_blank_lines_unchanged(self):
        lines = ["\n", "\n"]
        result = process_commit_message(lines, "stable/5.2.x")
        self.assertEqual(result, lines)