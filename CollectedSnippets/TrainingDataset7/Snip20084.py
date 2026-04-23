def test_https_reject_insecure_referer(self):
        """
        A POST HTTPS request from an insecure referer should be rejected.
        """
        req = self._get_POST_request_with_token()
        req._is_secure_override = True
        req.META["HTTP_REFERER"] = "http://example.com/"
        req.META["SERVER_PORT"] = "443"
        mw = CsrfViewMiddleware(post_form_view)
        response = mw.process_view(req, post_form_view, (), {})
        self.assertContains(
            response,
            "Referer checking failed - Referer is insecure while host is secure.",
            status_code=403,
        )