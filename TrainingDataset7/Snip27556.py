def test_questioner_no_default_syntax_error(self, mock_input):
        with self.assertRaises(SystemExit):
            self.questioner._ask_default()
        self.assertIn("SyntaxError: invalid syntax", self.prompt.getvalue())