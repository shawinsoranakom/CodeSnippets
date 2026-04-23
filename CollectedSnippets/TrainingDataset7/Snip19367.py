def test_session_cookie_secure_with_middleware(self):
        """
        Warn if SESSION_COOKIE_SECURE is off and
        "django.contrib.sessions.middleware.SessionMiddleware" is in
        MIDDLEWARE.
        """
        self.assertEqual(sessions.check_session_cookie_secure(None), [sessions.W011])