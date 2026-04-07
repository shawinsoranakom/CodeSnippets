def test_help_text(self):
        self.assertEqual(
            CommonPasswordValidator().get_help_text(),
            "Your password can’t be a commonly used password.",
        )