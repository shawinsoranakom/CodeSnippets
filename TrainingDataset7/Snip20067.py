def test_masked_secret_accepted_and_replaced(self):
        """
        For a view that uses the csrf_token, the csrf cookie is replaced with
        the unmasked version if originally masked.
        """
        req = self._get_POST_request_with_token(cookie=MASKED_TEST_SECRET1)
        mw = CsrfViewMiddleware(token_view)
        mw.process_request(req)
        resp = mw.process_view(req, token_view, (), {})
        self.assertIsNone(resp)
        resp = mw(req)
        csrf_cookie = self._read_csrf_cookie(req, resp)
        self.assertEqual(csrf_cookie, TEST_SECRET)
        self._check_token_present(resp, csrf_cookie)