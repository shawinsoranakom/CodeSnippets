def test_invalid_username(self):
        # The user submits an invalid username.

        data = {
            "username": "jsmith_does_not_exist",
            "password": "test123",
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