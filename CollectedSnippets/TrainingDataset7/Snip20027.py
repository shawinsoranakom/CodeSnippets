def test_https_no_referer(self):
        """A POST HTTPS request with a missing referer is rejected."""
        req = self._get_POST_request_with_token()
        req._is_secure_override = True
        mw = CsrfViewMiddleware(post_form_view)
        self._check_referer_rejects(mw, req)
        response = mw.process_view(req, post_form_view, (), {})
        self.assertContains(
            response,
            "Referer checking failed - no Referer.",
            status_code=403,
        )