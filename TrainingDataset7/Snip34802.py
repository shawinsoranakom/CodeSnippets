def test_logout_with_user(self):
        """Logout should send user_logged_out signal if user was logged in."""

        def listener(*args, **kwargs):
            listener.executed = True
            self.assertEqual(kwargs["sender"], User)

        listener.executed = False

        user_logged_out.connect(listener)
        self.client.login(username="testclient", password="password")
        self.client.logout()
        user_logged_out.disconnect(listener)
        self.assertTrue(listener.executed)