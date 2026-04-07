def test_content_length_header_added_to_append_slash_redirect(self):
        """
        The Content-Length header is set when redirecting with the APPEND_SLASH
        setting.
        """
        request = self.rf.get("/customurlconf/slash")
        request.urlconf = "middleware.extra_urls"
        r = CommonMiddleware(get_response_404)(request)
        self.assertEqual(r.status_code, 301)
        self.assertEqual(r.url, "/customurlconf/slash/")
        self.assertTrue(r.has_header("Content-Length"))