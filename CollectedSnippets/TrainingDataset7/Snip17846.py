def test_unusable_password(self):
        data = {
            "username": "new-user-which-does-not-exist",
            "usable_password": "false",
        }
        form = self.form_class(data)
        self.assertIs(form.is_valid(), True, form.errors)
        u = form.save()
        self.assertEqual(u.username, data["username"])
        self.assertFalse(u.has_usable_password())