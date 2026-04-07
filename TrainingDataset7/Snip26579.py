def test_append_slash_redirect_querystring(self):
        """
        APPEND_SLASH should preserve querystrings when redirecting.
        """
        request = self.rf.get("/slash?test=1")
        resp = CommonMiddleware(get_response_404)(request)
        self.assertEqual(resp.url, "/slash/?test=1")