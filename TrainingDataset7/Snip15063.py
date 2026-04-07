def test_capitalizes_first_letter(self):
        lines = ["fixed #123 -- Added a feature.\n"]
        result = process_commit_message(lines, "main")
        self.assertEqual(result[0], "Fixed #123 -- Added a feature.\n")