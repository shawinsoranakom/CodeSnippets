def test_https_good_referer_2(self):
        """
        A POST HTTPS request with a good referer is accepted where the referer
        contains no trailing slash.
        """
        # See ticket #15617
        req = self._get_POST_request_with_token()
        req._is_secure_override = True
        req.META["HTTP_HOST"] = "www.example.com"
        req.META["HTTP_REFERER"] = "https://www.example.com"
        mw = CsrfViewMiddleware(post_form_view)
        mw.process_request(req)
        resp = mw.process_view(req, post_form_view, (), {})
        self.assertIsNone(resp)