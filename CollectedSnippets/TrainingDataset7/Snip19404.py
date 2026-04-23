def test_no_ssl_redirect_no_middleware(self):
        """
        Don't warn if SECURE_SSL_REDIRECT is False and SecurityMiddleware isn't
        installed.
        """
        self.assertEqual(base.check_ssl_redirect(None), [])