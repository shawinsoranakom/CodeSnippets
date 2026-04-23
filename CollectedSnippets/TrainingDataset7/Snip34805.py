def test_logout_without_user(self):
        """Logout should send signal even if user not authenticated."""

        def listener(user, *args, **kwargs):
            listener.user = user
            listener.executed = True

        listener.executed = False

        user_logged_out.connect(listener)
        self.client.login(username="incorrect", password="password")
        self.client.logout()
        user_logged_out.disconnect(listener)

        self.assertTrue(listener.executed)
        self.assertIsNone(listener.user)