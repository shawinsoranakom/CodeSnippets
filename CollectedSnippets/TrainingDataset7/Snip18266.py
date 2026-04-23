def test_l10n(self, mock_ngettext):
        with self.subTest("get_error_message"):
            MinimumLengthValidator().get_error_message()
            mock_ngettext.assert_called_with(
                "This password is too short. It must contain at least %d character.",
                "This password is too short. It must contain at least %d characters.",
                8,
            )
        mock_ngettext.reset()
        with self.subTest("get_help_text"):
            MinimumLengthValidator().get_help_text()
            mock_ngettext.assert_called_with(
                "Your password must contain at least %(min_length)d " "character.",
                "Your password must contain at least %(min_length)d " "characters.",
                8,
            )