def test_ssl_redirect_off(self):
        """
        With SECURE_SSL_REDIRECT False, the middleware does not redirect.
        """
        ret = self.process_request("get", "/some/url")
        self.assertIsNone(ret)