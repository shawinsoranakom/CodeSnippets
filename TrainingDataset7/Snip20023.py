def test_token_node_with_new_csrf_cookie(self):
        """
        CsrfTokenNode works when a CSRF cookie is created by
        the middleware (when one was not already present)
        """
        req = self._get_request()
        mw = CsrfViewMiddleware(token_view)
        mw.process_view(req, token_view, (), {})
        resp = mw(req)
        csrf_cookie = self._read_csrf_cookie(req, resp)
        self._check_token_present(resp, csrf_cookie)