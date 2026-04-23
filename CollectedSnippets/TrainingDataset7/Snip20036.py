def test_https_csrf_wildcard_trusted_origin_allowed(self):
        """
        A POST HTTPS request with a referer that matches a CSRF_TRUSTED_ORIGINS
        wildcard is accepted.
        """
        req = self._get_POST_request_with_token()
        req._is_secure_override = True
        req.META["HTTP_HOST"] = "www.example.com"
        req.META["HTTP_REFERER"] = "https://dashboard.example.com"
        mw = CsrfViewMiddleware(post_form_view)
        mw.process_request(req)
        response = mw.process_view(req, post_form_view, (), {})
        self.assertIsNone(response)