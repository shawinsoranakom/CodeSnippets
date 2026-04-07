def test_session_cookie_secure_true(self):
        """
        If SESSION_COOKIE_SECURE is on, there's no warning about it.
        """
        self.assertEqual(sessions.check_session_cookie_secure(None), [])