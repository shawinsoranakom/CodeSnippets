def test_no_csrf_cookie(self):
        """
        If no CSRF cookies is present, the middleware rejects the incoming
        request. This will stop login CSRF.
        """
        self._check_bad_or_missing_cookie(None, REASON_NO_CSRF_COOKIE)