def test_process_view_token_too_long(self):
        """
        If the token is longer than expected, it is ignored and a new token is
        created.
        """
        req = self._get_request(cookie="x" * 100000)
        mw = CsrfViewMiddleware(token_view)
        mw.process_view(req, token_view, (), {})
        resp = mw(req)
        csrf_cookie = self._read_csrf_cookie(req, resp)
        self.assertEqual(len(csrf_cookie), CSRF_SECRET_LENGTH)