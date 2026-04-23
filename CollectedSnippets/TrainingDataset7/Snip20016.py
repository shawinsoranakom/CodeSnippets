def test_put_and_delete_allowed(self):
        """
        HTTP PUT and DELETE can get through with X-CSRFToken and a cookie.
        """
        req = self._get_csrf_cookie_request(
            method="PUT", meta_token=self._csrf_id_token
        )
        mw = CsrfViewMiddleware(post_form_view)
        mw.process_request(req)
        resp = mw.process_view(req, post_form_view, (), {})
        self.assertIsNone(resp)

        req = self._get_csrf_cookie_request(
            method="DELETE", meta_token=self._csrf_id_token
        )
        mw.process_request(req)
        resp = mw.process_view(req, post_form_view, (), {})
        self.assertIsNone(resp)