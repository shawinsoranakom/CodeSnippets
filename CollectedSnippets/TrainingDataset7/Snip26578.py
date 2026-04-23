def test_append_slash_redirect(self):
        """
        APPEND_SLASH should redirect slashless URLs to a valid pattern.
        """
        request = self.rf.get("/slash")
        r = CommonMiddleware(get_response_empty).process_request(request)
        self.assertIsNone(r)
        response = HttpResponseNotFound()
        r = CommonMiddleware(get_response_empty).process_response(request, response)
        self.assertEqual(r.status_code, 301)
        self.assertEqual(r.url, "/slash/")