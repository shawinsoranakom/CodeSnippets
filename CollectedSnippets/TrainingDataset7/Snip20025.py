def test_https_bad_referer(self):
        """
        A POST HTTPS request with a bad referer is rejected
        """
        req = self._get_POST_request_with_token()
        req._is_secure_override = True
        req.META["HTTP_HOST"] = "www.example.com"
        req.META["HTTP_REFERER"] = "https://www.evil.org/somepage"
        req.META["SERVER_PORT"] = "443"
        mw = CsrfViewMiddleware(post_form_view)
        response = mw.process_view(req, post_form_view, (), {})
        self.assertContains(
            response,
            "Referer checking failed - https://www.evil.org/somepage does not "
            "match any trusted origins.",
            status_code=403,
        )