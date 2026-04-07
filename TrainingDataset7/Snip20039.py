def test_ensures_csrf_cookie_no_logging(self):
        """
        ensure_csrf_cookie() doesn't log warnings (#19436).
        """
        with self.assertNoLogs("django.security.csrf", "WARNING"):
            req = self._get_request()
            ensure_csrf_cookie_view(req)