def test_bad_origin_cannot_be_parsed(self):
        """
        A POST request with an origin that can't be parsed by urlsplit() is
        rejected.
        """
        req = self._get_POST_request_with_token()
        req.META["HTTP_HOST"] = "www.example.com"
        req.META["HTTP_ORIGIN"] = "https://["
        mw = CsrfViewMiddleware(post_form_view)
        self._check_referer_rejects(mw, req)
        self.assertIs(mw._origin_verified(req), False)
        with self.assertLogs("django.security.csrf", "WARNING") as cm:
            response = mw.process_view(req, post_form_view, (), {})
        msg = REASON_BAD_ORIGIN % req.META["HTTP_ORIGIN"]
        self.assertForbiddenReason(response, cm, msg)