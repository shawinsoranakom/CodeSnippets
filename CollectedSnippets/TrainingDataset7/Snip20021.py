def test_get_token_for_exempt_view(self):
        """
        get_token still works for a view decorated with 'csrf_exempt'.
        """
        req = self._get_csrf_cookie_request()
        mw = CsrfViewMiddleware(token_view)
        mw.process_request(req)
        mw.process_view(req, csrf_exempt(token_view), (), {})
        resp = token_view(req)
        self._check_token_present(resp)