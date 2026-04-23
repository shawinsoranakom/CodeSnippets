def test_good_origin_csrf_trusted_origin_allowed(self):
        """
        A POST request with an origin added to the CSRF_TRUSTED_ORIGINS
        setting is accepted.
        """
        req = self._get_POST_request_with_token()
        req._is_secure_override = True
        req.META["HTTP_HOST"] = "www.example.com"
        req.META["HTTP_ORIGIN"] = "https://dashboard.example.com"
        mw = CsrfViewMiddleware(post_form_view)
        self.assertIs(mw._origin_verified(req), True)
        resp = mw.process_view(req, post_form_view, (), {})
        self.assertIsNone(resp)
        self.assertEqual(mw.allowed_origins_exact, {"https://dashboard.example.com"})
        self.assertEqual(mw.allowed_origin_subdomains, {})