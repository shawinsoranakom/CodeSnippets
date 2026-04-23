def test_bare_secret_accepted_and_not_replaced(self):
        """
        The csrf cookie is left unchanged if originally not masked.
        """
        req = self._get_POST_request_with_token(cookie=TEST_SECRET)
        mw = CsrfViewMiddleware(token_view)
        mw.process_request(req)
        resp = mw.process_view(req, token_view, (), {})
        self.assertIsNone(resp)
        resp = mw(req)
        csrf_cookie = self._read_csrf_cookie(req, resp)
        self.assertEqual(csrf_cookie, TEST_SECRET)
        self._check_token_present(resp, csrf_cookie)