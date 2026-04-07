def test_login_without_signal(self):
        """Login shouldn't send signal if user wasn't logged in"""

        def listener(*args, **kwargs):
            listener.executed = True

        listener.executed = False

        user_logged_in.connect(listener)
        self.client.login(username="incorrect", password="password")
        user_logged_in.disconnect(listener)

        self.assertFalse(listener.executed)