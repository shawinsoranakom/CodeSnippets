def test_reading_post_data_raises_unreadable_post_error(self):
        """
        An UnreadablePostError raised while reading the POST data should be
        handled by the middleware.
        """
        req = self._get_POST_request_with_token()
        mw = CsrfViewMiddleware(post_form_view)
        mw.process_request(req)
        resp = mw.process_view(req, post_form_view, (), {})
        self.assertIsNone(resp)

        req = self._get_POST_request_with_token(request_class=PostErrorRequest)
        req.post_error = UnreadablePostError("Error reading input data.")
        mw.process_request(req)
        with self.assertLogs("django.security.csrf", "WARNING") as cm:
            resp = mw.process_view(req, post_form_view, (), {})
        self.assertForbiddenReason(resp, cm, REASON_CSRF_TOKEN_MISSING)