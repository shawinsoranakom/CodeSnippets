def test_append_slash_disabled_custom_urlconf(self):
        """
        Disabling append slash functionality should leave slashless URLs alone.
        """
        request = self.rf.get("/customurlconf/slash")
        request.urlconf = "middleware.extra_urls"
        self.assertIsNone(CommonMiddleware(get_response_404).process_request(request))
        self.assertEqual(CommonMiddleware(get_response_404)(request).status_code, 404)