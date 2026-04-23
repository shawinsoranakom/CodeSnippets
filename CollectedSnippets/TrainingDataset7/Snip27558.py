def test_questioner_no_default_attribute_error(self, mock_input):
        with self.assertRaises(SystemExit):
            self.questioner._ask_default()
        self.assertIn(
            "AttributeError: module 'datetime' has no attribute 'dat'",
            self.prompt.getvalue(),
        )