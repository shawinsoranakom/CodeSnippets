def test_inactive_user_incorrect_password(self):
        """An invalid login doesn't leak the inactive status of a user."""
        data = {
            "username": "inactive",
            "password": "incorrect",
        }
        form = AuthenticationForm(None, data)
        self.assertFalse(form.is_valid())
        self.assertEqual(
            form.non_field_errors(),
            [
                form.error_messages["invalid_login"]
                % {"username": User._meta.get_field("username").verbose_name}
            ],
        )