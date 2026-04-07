def test_unicode_username(self):
        User.objects.create_user(username="Σαρα", password="pwd")
        data = {
            "username": "Σαρα",
            "password": "pwd",
        }
        form = AuthenticationForm(None, data)
        self.assertTrue(form.is_valid())
        self.assertEqual(form.non_field_errors(), [])