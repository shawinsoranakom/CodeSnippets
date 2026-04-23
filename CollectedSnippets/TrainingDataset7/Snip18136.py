def test_create_user_is_staff(self):
        email = "normal@normal.com"
        user = User.objects.create_user("user", email, is_staff=True)
        self.assertEqual(user.email, email)
        self.assertEqual(user.username, "user")
        self.assertTrue(user.is_staff)