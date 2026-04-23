def test_token_node_with_csrf_cookie(self):
        """
        CsrfTokenNode works when a CSRF cookie is set.
        """
        req = self._get_csrf_cookie_request()
        mw = CsrfViewMiddleware(token_view)
        mw.process_request(req)
        mw.process_view(req, token_view, (), {})
        resp = token_view(req)
        self._check_token_present(resp)