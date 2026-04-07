def _check_bad_or_missing_cookie(self, cookie, expected):
        """Passing None for cookie includes no cookie."""
        req = self._get_request(method="POST", cookie=cookie)
        mw = CsrfViewMiddleware(post_form_view)
        mw.process_request(req)
        with self.assertLogs("django.security.csrf", "WARNING") as cm:
            resp = mw.process_view(req, post_form_view, (), {})
        self.assertForbiddenReason(resp, cm, expected)