def test_append_slash_redirect_custom_urlconf(self):
        """
        APPEND_SLASH should redirect slashless URLs to a valid pattern.
        """
        request = self.rf.get("/customurlconf/slash")
        request.urlconf = "middleware.extra_urls"
        r = CommonMiddleware(get_response_404)(request)
        self.assertIsNotNone(
            r,
            "CommonMiddleware failed to return APPEND_SLASH redirect using "
            "request.urlconf",
        )
        self.assertEqual(r.status_code, 301)
        self.assertEqual(r.url, "/customurlconf/slash/")