def test_non_ascii_query_string_does_not_crash(self):
        """Regression test for #15152"""
        request = self.rf.get("/slash")
        request.META["QUERY_STRING"] = "drink=café"
        r = CommonMiddleware(get_response_empty).process_request(request)
        self.assertIsNone(r)
        response = HttpResponseNotFound()
        r = CommonMiddleware(get_response_empty).process_response(request, response)
        self.assertEqual(r.status_code, 301)