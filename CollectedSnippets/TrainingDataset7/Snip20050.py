def test_good_origin_wildcard_csrf_trusted_origin_allowed(self):
        """
        A POST request with an origin that matches a CSRF_TRUSTED_ORIGINS
        wildcard is accepted.
        """
        req = self._get_POST_request_with_token()
        req._is_secure_override = True
        req.META["HTTP_HOST"] = "www.example.com"
        req.META["HTTP_ORIGIN"] = "https://foo.example.com"
        mw = CsrfViewMiddleware(post_form_view)
        self.assertIs(mw._origin_verified(req), True)
        response = mw.process_view(req, post_form_view, (), {})
        self.assertIsNone(response)
        self.assertEqual(mw.allowed_origins_exact, set())
        self.assertEqual(mw.allowed_origin_subdomains, {"https": [".example.com"]})