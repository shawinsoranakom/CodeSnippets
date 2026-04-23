def test_no_password(self):
        user = User.objects.get(username="testclient")
        data = {"new_password1": "new-password"}
        form = SetPasswordForm(user, data)
        self.assertIs(form.is_valid(), False)
        self.assertEqual(
            form["new_password2"].errors, [Field.default_error_messages["required"]]
        )
        form = SetPasswordForm(user, {})
        self.assertIs(form.is_valid(), False)
        self.assertEqual(
            form["new_password1"].errors, [Field.default_error_messages["required"]]
        )
        self.assertEqual(
            form["new_password2"].errors, [Field.default_error_messages["required"]]
        )