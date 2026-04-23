def test_user_clean_normalize_email(self):
        user = User(username="user", password="foo", email="foo@BAR.com")
        user.clean()
        self.assertEqual(user.email, "foo@bar.com")