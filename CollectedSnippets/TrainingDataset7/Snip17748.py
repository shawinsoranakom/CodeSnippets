def test_validates_password(self):
        data = {
            "username": "otherclient",
            "password1": "otherclient",
            "password2": "otherclient",
        }
        form = self.form_class(data)
        self.assertFalse(form.is_valid())
        self.assertEqual(len(form["password2"].errors), 2)
        self.assertIn(
            "The password is too similar to the username.", form["password2"].errors
        )
        self.assertIn(
            "This password is too short. It must contain at least 12 characters.",
            form["password2"].errors,
        )