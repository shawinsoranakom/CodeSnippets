def test_append_slash_slashless_resource_custom_urlconf(self):
        """
        Matches to explicit slashless URLs should go unmolested.
        """

        def get_response(req):
            return HttpResponse("web content")

        request = self.rf.get("/customurlconf/noslash")
        request.urlconf = "middleware.extra_urls"
        self.assertIsNone(CommonMiddleware(get_response).process_request(request))
        self.assertEqual(
            CommonMiddleware(get_response)(request).content, b"web content"
        )