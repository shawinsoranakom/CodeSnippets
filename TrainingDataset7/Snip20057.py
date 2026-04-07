def test_csrf_cookie_age_none(self):
        """
        CSRF cookie age does not have max age set and therefore uses
        session-based cookies.
        """
        req = self._get_request()

        MAX_AGE = None
        with self.settings(
            CSRF_COOKIE_NAME="csrfcookie",
            CSRF_COOKIE_DOMAIN=".example.com",
            CSRF_COOKIE_AGE=MAX_AGE,
            CSRF_COOKIE_PATH="/test/",
            CSRF_COOKIE_SECURE=True,
            CSRF_COOKIE_HTTPONLY=True,
        ):
            # token_view calls get_token() indirectly
            mw = CsrfViewMiddleware(token_view)
            mw.process_view(req, token_view, (), {})
            resp = mw(req)
            max_age = resp.cookies.get("csrfcookie").get("max-age")
            self.assertEqual(max_age, "")