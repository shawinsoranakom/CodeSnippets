def test_help_text(self):
        self.assertEqual(
            MinimumLengthValidator().get_help_text(),
            "Your password must contain at least 8 characters.",
        )