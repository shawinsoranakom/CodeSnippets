def test_https_good_referer_malformed_host(self):
        """
        A POST HTTPS request is accepted if it receives a good referer with
        a bad host.
        """
        req = self._get_POST_request_with_token()
        req._is_secure_override = True
        req.META["HTTP_HOST"] = "@malformed"
        req.META["HTTP_REFERER"] = "https://dashboard.example.com/somepage"
        mw = CsrfViewMiddleware(post_form_view)
        mw.process_request(req)
        resp = mw.process_view(req, post_form_view, (), {})
        self.assertIsNone(resp)