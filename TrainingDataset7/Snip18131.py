def test_create_user(self):
        email_lowercase = "normal@normal.com"
        user = User.objects.create_user("user", email_lowercase)
        self.assertEqual(user.email, email_lowercase)
        self.assertEqual(user.username, "user")
        self.assertFalse(user.has_usable_password())