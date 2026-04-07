def _test_https_good_referer_matches_cookie_domain(self):
        req = self._get_POST_request_with_token()
        req._is_secure_override = True
        req.META["HTTP_REFERER"] = "https://foo.example.com/"
        req.META["SERVER_PORT"] = "443"
        mw = CsrfViewMiddleware(post_form_view)
        mw.process_request(req)
        response = mw.process_view(req, post_form_view, (), {})
        self.assertIsNone(response)