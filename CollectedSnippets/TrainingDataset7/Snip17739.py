def test_user_already_exists(self):
        data = {
            "username": "testclient",
            "password1": "test123",
            "password2": "test123",
        }
        form = self.form_class(data)
        self.assertFalse(form.is_valid())
        self.assertEqual(
            form["username"].errors,
            [str(User._meta.get_field("username").error_messages["unique"])],
        )