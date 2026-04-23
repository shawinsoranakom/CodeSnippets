def test_password_whitespace_not_stripped(self):
        user = User.objects.get(username="testclient")
        data = {
            "password1": " pass ",
            "password2": " pass ",
        }
        form = AdminPasswordChangeForm(user, data)
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data["password1"], data["password1"])
        self.assertEqual(form.cleaned_data["password2"], data["password2"])
        self.assertEqual(form.changed_data, ["password"])