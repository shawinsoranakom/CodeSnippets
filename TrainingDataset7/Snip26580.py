def test_append_slash_redirect_querystring_have_slash(self):
        """
        APPEND_SLASH should append slash to path when redirecting a request
        with a querystring ending with slash.
        """
        request = self.rf.get("/slash?test=slash/")
        resp = CommonMiddleware(get_response_404)(request)
        self.assertIsInstance(resp, HttpResponsePermanentRedirect)
        self.assertEqual(resp.url, "/slash/?test=slash/")