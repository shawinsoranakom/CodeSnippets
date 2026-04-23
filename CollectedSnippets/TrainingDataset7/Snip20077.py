def test_masked_unmasked_combinations(self):
        """
        Masked and unmasked tokens are allowed both as POST and as the
        X-CSRFToken header.
        """
        cases = [
            # Bare secrets are not allowed when CSRF_USE_SESSIONS=True.
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