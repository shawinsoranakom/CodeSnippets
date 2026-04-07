def test_ensures_csrf_cookie_no_middleware(self):
        """
        The ensure_csrf_cookie() decorator works without middleware.
        """
        req = self._get_request()
        resp = ensure_csrf_cookie_view(req)
        csrf_cookie = self._read_csrf_cookie(req, resp)
        self.assertTrue(csrf_cookie)
        self.assertIn("Cookie", resp.get("Vary", ""))