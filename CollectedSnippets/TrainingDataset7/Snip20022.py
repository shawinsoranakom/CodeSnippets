def test_get_token_for_requires_csrf_token_view(self):
        """
        get_token() works for a view decorated solely with requires_csrf_token.
        """
        req = self._get_csrf_cookie_request()
        resp = requires_csrf_token(token_view)(req)
        self._check_token_present(resp)