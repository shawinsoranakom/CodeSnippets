def test_validates_password(self):
        user = User.objects.get(username="testclient")
        data = {
            "password1": "testclient",
            "password2": "testclient",
        }
        form = AdminPasswordChangeForm(user, data)
        self.assertFalse(form.is_valid())
        self.assertEqual(len(form["password2"].errors), 2)
        self.assertIn(
            "The password is too similar to the username.",
            form["password2"].errors,
        )
        self.assertIn(
            "This password is too short. It must contain at least 12 characters.",
            form["password2"].errors,
        )

        # passwords are not validated if `usable_password` is unset
        data = {
            "password1": "testclient",
            "password2": "testclient",
            "usable_password": "false",
        }
        form = AdminPasswordChangeForm(user, data)
        self.assertIs(form.is_valid(), True, form.errors)