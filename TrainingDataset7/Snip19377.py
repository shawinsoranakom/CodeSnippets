def test_with_csrf_cookie_secure_false(self):
        """
        Warn if CsrfViewMiddleware is in MIDDLEWARE but
        CSRF_COOKIE_SECURE isn't True.
        """
        self.assertEqual(csrf.check_csrf_cookie_secure(None), [csrf.W016])