def test_prepend_www_append_slash_have_slash_custom_urlconf(self):
        request = self.rf.get("/customurlconf/slash/")
        request.urlconf = "middleware.extra_urls"
        r = CommonMiddleware(get_response_empty).process_request(request)
        self.assertEqual(r.status_code, 301)
        self.assertEqual(r.url, "http://www.testserver/customurlconf/slash/")