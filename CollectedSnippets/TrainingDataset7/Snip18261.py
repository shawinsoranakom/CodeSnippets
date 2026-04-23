def test_password_validators_help_text_html(self):
        help_text = password_validators_help_text_html()
        self.assertEqual(help_text.count("<li>"), 2)
        self.assertIn("12 characters", help_text)