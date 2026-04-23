def test_with_csrf_cookie_secure_false_no_middleware(self):
        """
        No warning if CsrfViewMiddleware isn't in MIDDLEWARE, even if
        CSRF_COOKIE_SECURE is False.
        """
        self.assertEqual(csrf.check_csrf_cookie_secure(None), [])