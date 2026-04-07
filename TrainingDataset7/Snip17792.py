def test_success(self, password_changed):
        # The success case.
        user = User.objects.get(username="testclient")
        data = {
            "old_password": "password",
            "new_password1": "abc123",
            "new_password2": "abc123",
        }
        form = PasswordChangeForm(user, data)
        self.assertTrue(form.is_valid())
        form.save(commit=False)
        self.assertEqual(password_changed.call_count, 0)
        form.save()
        self.assertEqual(password_changed.call_count, 1)