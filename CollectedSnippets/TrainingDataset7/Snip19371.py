def test_session_cookie_httponly_with_installed_app_truthy(self):
        """SESSION_COOKIE_HTTPONLY must be boolean."""
        self.assertEqual(sessions.check_session_cookie_httponly(None), [sessions.W013])