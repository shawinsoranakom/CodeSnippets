def test_password_validators_help_texts(self):
        help_texts = password_validators_help_texts()
        self.assertEqual(len(help_texts), 2)
        self.assertIn("12 characters", help_texts[1])

        self.assertEqual(password_validators_help_texts(password_validators=[]), [])