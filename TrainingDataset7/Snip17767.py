def test_inactive_user_i18n(self):
        with (
            self.settings(USE_I18N=True),
            translation.override("pt-br", deactivate=True),
        ):
            # The user is inactive.
            data = {
                "username": "inactive",
                "password": "password",
            }
            form = AuthenticationForm(None, data)
            self.assertFalse(form.is_valid())
            self.assertEqual(
                form.non_field_errors(), [str(form.error_messages["inactive"])]
            )