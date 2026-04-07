def test_cookie_not_reset_on_accepted_request(self):
        """
        The csrf token used in posts is changed on every request (although
        stays equivalent). The csrf cookie should not change on accepted
        requests. If it appears in the response, it should keep its value.
        """
        req = self._get_POST_request_with_token()
        mw = CsrfViewMiddleware(token_view)
        mw.process_request(req)
        mw.process_view(req, token_view, (), {})
        resp = mw(req)
        csrf_cookie = self._read_csrf_cookie(req, resp)
        self.assertEqual(
            csrf_cookie,
            TEST_SECRET,
            "CSRF cookie was changed on an accepted request",
        )