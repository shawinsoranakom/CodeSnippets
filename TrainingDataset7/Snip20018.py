def test_token_node_no_csrf_cookie(self):
        """
        CsrfTokenNode works when no CSRF cookie is set.
        """
        req = self._get_request()
        resp = token_view(req)

        token = get_token(req)
        self.assertIsNotNone(token)
        csrf_secret = _unmask_cipher_token(token)
        self._check_token_present(resp, csrf_secret)