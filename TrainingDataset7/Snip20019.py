def test_token_node_empty_csrf_cookie(self):
        """
        A new token is sent if the csrf_cookie is the empty string.
        """
        req = self._get_request(cookie="")
        mw = CsrfViewMiddleware(token_view)
        mw.process_view(req, token_view, (), {})
        resp = token_view(req)

        token = get_token(req)
        self.assertIsNotNone(token)
        csrf_secret = _unmask_cipher_token(token)
        self._check_token_present(resp, csrf_secret)