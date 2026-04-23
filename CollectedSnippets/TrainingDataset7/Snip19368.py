def test_session_cookie_secure_both(self):
        """
        If SESSION_COOKIE_SECURE is off and we find both the session app and
        the middleware, provide one common warning.
        """
        self.assertEqual(sessions.check_session_cookie_secure(None), [sessions.W012])