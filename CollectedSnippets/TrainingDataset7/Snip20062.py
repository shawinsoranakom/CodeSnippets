def test_process_view_token_invalid_chars(self):
        """
        If the token contains non-alphanumeric characters, it is ignored and a
        new token is created.
        """
        token = ("!@#" + self._csrf_id_token)[:CSRF_TOKEN_LENGTH]
        req = self._get_request(cookie=token)
        mw = CsrfViewMiddleware(token_view)
        mw.process_view(req, token_view, (), {})
        resp = mw(req)
        csrf_cookie = self._read_csrf_cookie(req, resp)
        self.assertEqual(len(csrf_cookie), CSRF_SECRET_LENGTH)
        self.assertNotEqual(csrf_cookie, token)