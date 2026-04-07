def test_capitalizes_first_letter_after_existing_prefix(self):
        lines = ["[5.2.x] fixed #123 -- Added a feature.\n"]
        result = process_commit_message(lines, "stable/5.2.x")
        self.assertTrue(result[0].startswith("[5.2.x] Fixed"))