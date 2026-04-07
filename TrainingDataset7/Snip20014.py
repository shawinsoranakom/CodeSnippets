def test_csrf_token_in_header_with_customized_name(self):
        """
        settings.CSRF_HEADER_NAME can be used to customize the CSRF header name
        """
        req = self._get_POST_csrf_cookie_request(
            meta_token=self._csrf_id_token,
            token_header="HTTP_X_CSRFTOKEN_CUSTOMIZED",
        )
        mw = CsrfViewMiddleware(post_form_view)
        mw.process_request(req)
        resp = mw.process_view(req, post_form_view, (), {})
        self.assertIsNone(resp)