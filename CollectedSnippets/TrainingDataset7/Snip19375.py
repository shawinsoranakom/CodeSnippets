def test_no_csrf_middleware(self):
        """
        Warn if CsrfViewMiddleware isn't in MIDDLEWARE.
        """
        self.assertEqual(csrf.check_csrf_middleware(None), [csrf.W003])