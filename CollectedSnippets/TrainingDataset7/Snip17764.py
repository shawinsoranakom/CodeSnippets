def test_inactive_user(self):
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