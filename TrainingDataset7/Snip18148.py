def test_last_login_default(self):
        user1 = User.objects.create(username="user1")
        self.assertIsNone(user1.last_login)

        user2 = User.objects.create_user(username="user2")
        self.assertIsNone(user2.last_login)