def test_process_response_get_token_used(self):
        """The ensure_csrf_cookie() decorator works without middleware."""
        req = self._get_request()
        ensure_csrf_cookie_view(req)
        csrf_cookie = self._read_csrf_cookie(req)
        self.assertTrue(csrf_cookie)