def test_success(self, password_changed):
        user = User.objects.get(username="testclient")
        data = {
            "new_password1": "abc123",
            "new_password2": "abc123",
        }
        form = SetPasswordForm(user, data)
        self.assertTrue(form.is_valid())
        form.save(commit=False)
        self.assertEqual(password_changed.call_count, 0)
        form.save()
        self.assertEqual(password_changed.call_count, 1)