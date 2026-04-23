def test_questioner_no_default_no_user_entry(self, mock_input):
        with self.assertRaises(SystemExit):
            self.questioner._ask_default()
        self.assertIn(
            "Please enter some code, or 'exit' (without quotes) to exit.",
            self.prompt.getvalue(),
        )