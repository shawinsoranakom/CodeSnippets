def test_rotate_token_triggers_second_reset(self):
        """
        If rotate_token() is called after the token is reset in
        CsrfViewMiddleware's process_response() and before another call to
        the same process_response(), the cookie is reset a second time.
        """
        req = self._get_POST_request_with_token()
        resp = sandwiched_rotate_token_view(req)
        self.assertContains(resp, "OK")
        actual_secret = self._read_csrf_cookie(req, resp)
        # set_cookie() was called a second time with a different secret.
        cookies_set = self._get_cookies_set(req, resp)
        # Only compare the last two to exclude a spurious entry that's present
        # when CsrfViewMiddlewareUseSessionsTests is running.
        self.assertEqual(cookies_set[-2:], [TEST_SECRET, actual_secret])
        self.assertNotEqual(actual_secret, TEST_SECRET)