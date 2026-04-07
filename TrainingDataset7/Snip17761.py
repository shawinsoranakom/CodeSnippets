def test_case_insensitive_username(self):
        data = {
            "username": "TeStClIeNt",
            "password1": "test123",
            "password2": "test123",
        }
        form = UserCreationForm(data)
        self.assertFalse(form.is_valid())
        self.assertEqual(
            form["username"].errors,
            ["A user with that username already exists."],
        )