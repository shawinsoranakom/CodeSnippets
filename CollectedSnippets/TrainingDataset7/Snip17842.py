def test_enable_password_authentication(self):
        user = User.objects.get(username="unusable_password")
        form = AdminPasswordChangeForm(
            user,
            {"password1": "complexpassword", "password2": "complexpassword"},
        )
        self.assertNotIn("usable_password", form.fields)
        self.assertIs(form.is_valid(), True)
        user = form.save(commit=True)
        self.assertIs(user.has_usable_password(), True)