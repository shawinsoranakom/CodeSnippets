def test_session_cookie_httponly_true(self):
        """
        If SESSION_COOKIE_HTTPONLY is on, there's no warning about it.
        """
        self.assertEqual(sessions.check_session_cookie_httponly(None), [])