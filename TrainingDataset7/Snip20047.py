def test_good_origin_insecure(self):
        """A POST HTTP request with a good origin is accepted."""
        req = self._get_POST_request_with_token()
        req.META["HTTP_HOST"] = "www.example.com"
        req.META["HTTP_ORIGIN"] = "http://www.example.com"
        mw = CsrfViewMiddleware(post_form_view)
        self.assertIs(mw._origin_verified(req), True)
        response = mw.process_view(req, post_form_view, (), {})
        self.assertIsNone(response)