def _check_bad_or_missing_token(
        self,
        expected,
        post_token=None,
        meta_token=None,
        token_header=None,
    ):
        req = self._get_POST_csrf_cookie_request(
            post_token=post_token,
            meta_token=meta_token,
            token_header=token_header,
        )
        mw = CsrfViewMiddleware(post_form_view)
        mw.process_request(req)
        with self.assertLogs("django.security.csrf", "WARNING") as cm:
            resp = mw.process_view(req, post_form_view, (), {})
        self.assertEqual(resp["Content-Type"], "text/html; charset=utf-8")
        self.assertForbiddenReason(resp, cm, expected)