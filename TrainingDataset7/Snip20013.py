def test_csrf_token_in_header(self):
        """
        The token may be passed in a header instead of in the form.
        """
        req = self._get_POST_csrf_cookie_request(meta_token=self._csrf_id_token)
        mw = CsrfViewMiddleware(post_form_view)
        mw.process_request(req)
        resp = mw.process_view(req, post_form_view, (), {})
        self.assertIsNone(resp)