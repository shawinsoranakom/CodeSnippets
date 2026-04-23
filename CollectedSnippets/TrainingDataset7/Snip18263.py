def test_empty_password_validator_help_text_html(self):
        self.assertEqual(password_validators_help_text_html(), "")