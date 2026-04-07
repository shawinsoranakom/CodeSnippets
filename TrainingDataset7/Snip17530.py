def test_login(self):
        """
        A custom user with a UUID primary key should be able to login.
        """
        user = UUIDUser.objects.create_user(username="uuid", password="test")
        self.assertTrue(self.client.login(username="uuid", password="test"))
        self.assertEqual(
            UUIDUser.objects.get(pk=self.client.session[SESSION_KEY]), user
        )