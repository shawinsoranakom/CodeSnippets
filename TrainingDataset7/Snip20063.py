def test_masked_unmasked_combinations(self):
        """
        All combinations are allowed of (1) masked and unmasked cookies,
        (2) masked and unmasked tokens, and (3) tokens provided via POST and
        the X-CSRFToken header.
        """
        cases = [
            (TEST_SECRET, TEST_SECRET, None),
            (TEST_SECRET, MASKED_TEST_SECRET2, None),
            (TEST_SECRET, None, TEST_SECRET),
            (TEST_SECRET, None, MASKED_TEST_SECRET2),
            (MASKED_TEST_SECRET1, TEST_SECRET, None),
            (MASKED_TEST_SECRET1, MASKED_TEST_SECRET2, None),
            (MASKED_TEST_SECRET1, None, TEST_SECRET),
            (MASKED_TEST_SECRET1, None, MASKED_TEST_SECRET2),
        ]
        for args in cases:
            with self.subTest(args=args):
                cookie, post_token, meta_token = args
                req = self._get_POST_csrf_cookie_request(
                    cookie=cookie,
                    post_token=post_token,
                    meta_token=meta_token,
                )
                mw = CsrfViewMiddleware(token_view)
                mw.process_request(req)
                resp = mw.process_view(req, token_view, (), {})
                self.assertIsNone(resp)