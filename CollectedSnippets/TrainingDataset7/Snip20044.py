def test_bad_origin_bad_protocol(self):
        """A request with an origin with wrong protocol is rejected."""
        req = self._get_POST_request_with_token()
        req._is_secure_override = True
        req.META["HTTP_HOST"] = "www.example.com"
        req.META["HTTP_ORIGIN"] = "http://example.com"
        mw = CsrfViewMiddleware(post_form_view)
        self._check_referer_rejects(mw, req)
        self.assertIs(mw._origin_verified(req), False)
        with self.assertLogs("django.security.csrf", "WARNING") as cm:
            response = mw.process_view(req, post_form_view, (), {})
        msg = REASON_BAD_ORIGIN % req.META["HTTP_ORIGIN"]
        self.assertForbiddenReason(response, cm, msg)