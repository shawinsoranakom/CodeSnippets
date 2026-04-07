def test_unicode_username(self):
        data = {
            "username": "宝",
            "password1": "test123",
            "password2": "test123",
        }
        form = self.form_class(data)
        self.assertTrue(form.is_valid())
        u = form.save()
        self.assertEqual(u.username, "宝")