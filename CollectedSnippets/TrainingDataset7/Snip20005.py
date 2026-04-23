def test_process_response_get_token_not_used(self):
        """
        If get_token() is not called, the view middleware does not
        add a cookie.
        """
        # This is important to make pages cacheable. Pages which do call
        # get_token(), assuming they use the token, are not cacheable because
        # the token is specific to the user
        req = self._get_request()
        # non_token_view_using_request_processor does not call get_token(), but
        # does use the csrf request processor. By using this, we are testing
        # that the view processor is properly lazy and doesn't call get_token()
        # until needed.
        mw = CsrfViewMiddleware(non_token_view_using_request_processor)
        mw.process_request(req)
        mw.process_view(req, non_token_view_using_request_processor, (), {})
        resp = mw(req)

        csrf_cookie = self._read_csrf_cookie(req, resp)
        self.assertIs(csrf_cookie, False)