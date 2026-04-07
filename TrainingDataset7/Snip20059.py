def test_bad_csrf_cookie_characters(self):
        """
        If the CSRF cookie has invalid characters in a POST request, the
        middleware rejects the incoming request.
        """
        self._check_bad_or_missing_cookie(
            64 * "*", "CSRF cookie has invalid characters."
        )