def test_login_with_user(self):
        """Login should send user_logged_in signal on successful login."""

        def listener(*args, **kwargs):
            listener.executed = True

        listener.executed = False

        user_logged_in.connect(listener)
        self.client.login(username="testclient", password="password")
        user_logged_out.disconnect(listener)

        self.assertTrue(listener.executed)