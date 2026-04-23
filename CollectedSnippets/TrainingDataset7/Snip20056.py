def test_csrf_cookie_age(self):
        """
        CSRF cookie age can be set using settings.CSRF_COOKIE_AGE.
        """
        req = self._get_request()

        MAX_AGE = 123
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
            self.assertEqual(max_age, MAX_AGE)