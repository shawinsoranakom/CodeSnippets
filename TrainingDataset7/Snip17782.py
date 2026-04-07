def test_password_verification(self):
        # The two new passwords do not match.
        user = User.objects.get(username="testclient")
        data = {
            "new_password1": "abc123",
            "new_password2": "abc",
        }
        form = SetPasswordForm(user, data)
        self.assertFalse(form.is_valid())
        self.assertEqual(
            form["new_password2"].errors,
            [str(form.error_messages["password_mismatch"])],
        )