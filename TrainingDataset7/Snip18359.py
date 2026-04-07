def test_session_key_flushed_on_login(self):
        """
        To avoid reusing another user's session, ensure a new, empty session is
        created if the existing session corresponds to a different
        authenticated user.
        """
        self.login()
        original_session_key = self.client.session.session_key

        self.login(username="staff")
        self.assertNotEqual(original_session_key, self.client.session.session_key)