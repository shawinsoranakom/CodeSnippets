def test_success(self, password_changed):
        user = User.objects.get(username="testclient")
        data = {
            "password1": "test123",
            "password2": "test123",
        }
        form = AdminPasswordChangeForm(user, data)
        self.assertTrue(form.is_valid())
        form.save(commit=False)
        self.assertEqual(password_changed.call_count, 0)
        form.save()
        self.assertEqual(password_changed.call_count, 1)
        self.assertEqual(form.changed_data, ["password"])