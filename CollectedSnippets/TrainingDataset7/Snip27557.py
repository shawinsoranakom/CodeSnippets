def test_questioner_no_default_name_error(self, mock_input):
        with self.assertRaises(SystemExit):
            self.questioner._ask_default()
        self.assertIn(
            "NameError: name 'datetim' is not defined", self.prompt.getvalue()
        )