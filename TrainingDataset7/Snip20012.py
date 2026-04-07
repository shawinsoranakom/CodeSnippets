def test_process_request_csrf_cookie_no_token_exempt_view(self):
        """
        If a CSRF cookie is present and no token, but the csrf_exempt decorator
        has been applied to the view, the middleware lets it through
        """
        req = self._get_POST_csrf_cookie_request()
        mw = CsrfViewMiddleware(post_form_view)
        mw.process_request(req)
        resp = mw.process_view(req, csrf_exempt(post_form_view), (), {})
        self.assertIsNone(resp)