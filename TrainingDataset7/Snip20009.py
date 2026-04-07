def test_csrf_cookie_bad_or_missing_token(self):
        """
        If a CSRF cookie is present but the token is missing or invalid, the
        middleware rejects the incoming request.
        """
        cases = [
            (None, None, REASON_CSRF_TOKEN_MISSING),
            (16 * "a", None, "CSRF token from POST has incorrect length."),
            (64 * "*", None, "CSRF token from POST has invalid characters."),
            (64 * "a", None, "CSRF token from POST incorrect."),
            (
                None,
                16 * "a",
                "CSRF token from the 'X-Csrftoken' HTTP header has incorrect length.",
            ),
            (
                None,
                64 * "*",
                "CSRF token from the 'X-Csrftoken' HTTP header has invalid characters.",
            ),
            (
                None,
                64 * "a",
                "CSRF token from the 'X-Csrftoken' HTTP header incorrect.",
            ),
        ]
        for post_token, meta_token, expected in cases:
            with self.subTest(post_token=post_token, meta_token=meta_token):
                self._check_bad_or_missing_token(
                    expected,
                    post_token=post_token,
                    meta_token=meta_token,
                )