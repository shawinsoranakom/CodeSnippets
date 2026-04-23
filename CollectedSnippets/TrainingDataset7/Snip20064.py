def test_set_cookie_called_only_once(self):
        """
        set_cookie() is called only once when the view is decorated with both
        ensure_csrf_cookie and csrf_protect.
        """
        req = self._get_POST_request_with_token()
        resp = ensured_and_protected_view(req)
        self.assertContains(resp, "OK")
        csrf_cookie = self._read_csrf_cookie(req, resp)
        self.assertEqual(csrf_cookie, TEST_SECRET)
        # set_cookie() was called only once and with the expected secret.
        cookies_set = self._get_cookies_set(req, resp)
        self.assertEqual(cookies_set, [TEST_SECRET])