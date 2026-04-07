def test_superuser_no_email_or_password(self):
        cases = [
            {},
            {"email": ""},
            {"email": None},
            {"password": None},
        ]
        for i, kwargs in enumerate(cases):
            with self.subTest(**kwargs):
                superuser = User.objects.create_superuser("super{}".format(i), **kwargs)
                self.assertEqual(superuser.email, "")
                self.assertFalse(superuser.has_usable_password())