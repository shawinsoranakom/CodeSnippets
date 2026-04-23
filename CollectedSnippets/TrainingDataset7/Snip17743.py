def test_success(self, password_changed):
        # The success case.
        data = {
            "username": "jsmith@example.com",
            "password1": "test123",
            "password2": "test123",
        }
        form = self.form_class(data)
        self.assertTrue(form.is_valid())
        form.save(commit=False)
        self.assertEqual(password_changed.call_count, 0)
        u = form.save()
        self.assertEqual(password_changed.call_count, 1)
        self.assertEqual(repr(u), "<User: jsmith@example.com>")