def test_prepend_www(self):
        request = self.rf.get("/path/")
        r = CommonMiddleware(get_response_empty).process_request(request)
        self.assertEqual(r.status_code, 301)
        self.assertEqual(r.url, "http://www.testserver/path/")