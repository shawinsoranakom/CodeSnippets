def test_session_modify(self):
        """The session isn't saved if the CSRF cookie is unchanged."""
        req = self._get_request()
        mw = CsrfViewMiddleware(ensure_csrf_cookie_view)
        mw.process_view(req, ensure_csrf_cookie_view, (), {})
        mw(req)
        csrf_cookie = self._read_csrf_cookie(req)
        self.assertTrue(csrf_cookie)
        req.session.modified = False
        mw.process_view(req, ensure_csrf_cookie_view, (), {})
        mw(req)
        self.assertFalse(req.session.modified)