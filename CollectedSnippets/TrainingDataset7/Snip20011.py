def test_process_request_csrf_cookie_and_token(self):
        """
        If both a cookie and a token is present, the middleware lets it
        through.
        """
        req = self._get_POST_request_with_token()
        mw = CsrfViewMiddleware(post_form_view)
        mw.process_request(req)
        resp = mw.process_view(req, post_form_view, (), {})
        self.assertIsNone(resp)