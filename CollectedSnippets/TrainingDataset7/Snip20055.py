def test_ensures_csrf_cookie_with_middleware(self):
        """
        The ensure_csrf_cookie() decorator works with the CsrfViewMiddleware
        enabled.
        """
        req = self._get_request()
        mw = CsrfViewMiddleware(ensure_csrf_cookie_view)
        mw.process_view(req, ensure_csrf_cookie_view, (), {})
        resp = mw(req)
        csrf_cookie = self._read_csrf_cookie(req, resp)
        self.assertTrue(csrf_cookie)
        self.assertIn("Cookie", resp.get("Vary", ""))