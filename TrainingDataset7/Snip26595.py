def test_append_slash_quoted_custom_urlconf(self):
        """
        URLs which require quoting should be redirected to their slash version.
        """
        request = self.rf.get(quote("/customurlconf/needsquoting#"))
        request.urlconf = "middleware.extra_urls"
        r = CommonMiddleware(get_response_404)(request)
        self.assertIsNotNone(
            r,
            "CommonMiddleware failed to return APPEND_SLASH redirect using "
            "request.urlconf",
        )
        self.assertEqual(r.status_code, 301)
        self.assertEqual(r.url, "/customurlconf/needsquoting%23/")