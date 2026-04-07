def test_csrf_cookie_bad_token_custom_header(self):
        """
        If a CSRF cookie is present and an invalid token is passed via a
        custom CSRF_HEADER_NAME, the middleware rejects the incoming request.
        """
        expected = (
            "CSRF token from the 'X-Csrftoken-Customized' HTTP header has "
            "incorrect length."
        )
        self._check_bad_or_missing_token(
            expected,
            meta_token=16 * "a",
            token_header="HTTP_X_CSRFTOKEN_CUSTOMIZED",
        )