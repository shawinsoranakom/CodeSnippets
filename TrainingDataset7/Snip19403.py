def test_no_ssl_redirect(self):
        """
        Warn if SECURE_SSL_REDIRECT isn't True.
        """
        self.assertEqual(base.check_ssl_redirect(None), [base.W008])