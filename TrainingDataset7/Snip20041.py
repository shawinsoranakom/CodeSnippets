def test_reading_post_data_raises_os_error(self):
        """
        An OSError raised while reading the POST data should not be handled by
        the middleware.
        """
        mw = CsrfViewMiddleware(post_form_view)
        req = self._get_POST_request_with_token(request_class=PostErrorRequest)
        req.post_error = OSError("Deleted directories/Missing permissions.")
        mw.process_request(req)
        with self.assertRaises(OSError):
            mw.process_view(req, post_form_view, (), {})