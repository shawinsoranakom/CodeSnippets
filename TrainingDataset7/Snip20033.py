def _test_https_good_referer_behind_proxy(self):
        req = self._get_POST_request_with_token()
        req._is_secure_override = True
        req.META.update(
            {
                "HTTP_HOST": "10.0.0.2",
                "HTTP_REFERER": "https://www.example.com/somepage",
                "SERVER_PORT": "8080",
                "HTTP_X_FORWARDED_HOST": "www.example.com",
                "HTTP_X_FORWARDED_PORT": "443",
            }
        )
        mw = CsrfViewMiddleware(post_form_view)
        mw.process_request(req)
        resp = mw.process_view(req, post_form_view, (), {})
        self.assertIsNone(resp)