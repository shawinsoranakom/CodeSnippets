def test_password_whitespace_not_stripped(self):
        user = User.objects.get(username="testclient")
        user.set_password("   oldpassword   ")
        data = {
            "old_password": "   oldpassword   ",
            "new_password1": " pass ",
            "new_password2": " pass ",
        }
        form = PasswordChangeForm(user, data)
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data["old_password"], data["old_password"])
        self.assertEqual(form.cleaned_data["new_password1"], data["new_password1"])
        self.assertEqual(form.cleaned_data["new_password2"], data["new_password2"])