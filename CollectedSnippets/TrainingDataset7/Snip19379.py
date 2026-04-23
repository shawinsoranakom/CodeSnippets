def test_use_sessions_with_csrf_cookie_secure_false(self):
        """
        No warning if CSRF_COOKIE_SECURE isn't True while CSRF_USE_SESSIONS
        is True.
        """
        self.assertEqual(csrf.check_csrf_cookie_secure(None), [])