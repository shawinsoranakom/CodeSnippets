def test_session_cookie_httponly_with_installed_app(self):
        """
        Warn if SESSION_COOKIE_HTTPONLY is off and "django.contrib.sessions"
        is in INSTALLED_APPS.
        """
        self.assertEqual(sessions.check_session_cookie_httponly(None), [sessions.W013])