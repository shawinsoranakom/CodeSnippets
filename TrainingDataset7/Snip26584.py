def test_append_slash_quoted(self):
        """
        URLs which require quoting should be redirected to their slash version.
        """
        request = self.rf.get(quote("/needsquoting#"))
        r = CommonMiddleware(get_response_404)(request)
        self.assertEqual(r.status_code, 301)
        self.assertEqual(r.url, "/needsquoting%23/")