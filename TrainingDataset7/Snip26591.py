def test_append_slash_slashless_unknown_custom_urlconf(self):
        """
        APPEND_SLASH should not redirect to unknown resources.
        """
        request = self.rf.get("/customurlconf/unknown")
        request.urlconf = "middleware.extra_urls"
        self.assertIsNone(CommonMiddleware(get_response_404).process_request(request))
        self.assertEqual(CommonMiddleware(get_response_404)(request).status_code, 404)