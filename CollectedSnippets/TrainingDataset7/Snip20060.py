def test_bad_csrf_cookie_length(self):
        """
        If the CSRF cookie has an incorrect length in a POST request, the
        middleware rejects the incoming request.
        """
        self._check_bad_or_missing_cookie(16 * "a", "CSRF cookie has incorrect length.")