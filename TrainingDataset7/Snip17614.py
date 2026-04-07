def test_user_no_email(self):
        "Users can be created without an email"
        cases = [
            {},
            {"email": ""},
            {"email": None},
        ]
        for i, kwargs in enumerate(cases):
            with self.subTest(**kwargs):
                u = User.objects.create_user("testuser{}".format(i), **kwargs)
                self.assertEqual(u.email, "")