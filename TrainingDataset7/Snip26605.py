def test_response_redirect_class(self):
        request = self.rf.get("/slash")
        r = CommonMiddleware(get_response_404)(request)
        self.assertEqual(r.status_code, 301)
        self.assertEqual(r.url, "/slash/")
        self.assertIsInstance(r, HttpResponsePermanentRedirect)