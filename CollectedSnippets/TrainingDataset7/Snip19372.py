def test_session_cookie_httponly_with_middleware(self):
        """
        Warn if SESSION_COOKIE_HTTPONLY is off and
        "django.contrib.sessions.middleware.SessionMiddleware" is in
        MIDDLEWARE.
        """
        self.assertEqual(sessions.check_session_cookie_httponly(None), [sessions.W014])