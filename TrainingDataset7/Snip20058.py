def test_csrf_cookie_samesite(self):
        req = self._get_request()
        with self.settings(
            CSRF_COOKIE_NAME="csrfcookie", CSRF_COOKIE_SAMESITE="Strict"
        ):
            mw = CsrfViewMiddleware(token_view)
            mw.process_view(req, token_view, (), {})
            resp = mw(req)
            self.assertEqual(resp.cookies["csrfcookie"]["samesite"], "Strict")