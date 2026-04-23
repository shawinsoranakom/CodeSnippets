def test_session_cookie_httponly_both(self):
        """
        If SESSION_COOKIE_HTTPONLY is off and we find both the session app and
        the middleware, provide one common warning.
        """
        self.assertEqual(sessions.check_session_cookie_httponly(None), [sessions.W015])