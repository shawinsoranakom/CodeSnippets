def test_disable_password_authentication(self):
        user = User.objects.get(username="testclient")
        form = AdminPasswordChangeForm(
            user,
            {"usable_password": "false", "password1": "", "password2": "test"},
        )
        self.assertIn("usable_password", form.fields)
        self.assertIn(
            "If disabled, the current password for this user will be lost.",
            form.fields["usable_password"].help_text,
        )
        self.assertIs(form.is_valid(), True)  # Valid despite password empty/mismatch.
        user = form.save(commit=True)
        self.assertIs(user.has_usable_password(), False)