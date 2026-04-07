def test_help_text(self):
        self.assertEqual(
            NumericPasswordValidator().get_help_text(),
            "Your password can’t be entirely numeric.",
        )