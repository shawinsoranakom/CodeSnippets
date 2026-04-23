def test_session_cookie_secure_with_installed_app_truthy(self):
        """SESSION_COOKIE_SECURE must be boolean."""
        self.assertEqual(sessions.check_session_cookie_secure(None), [sessions.W010])