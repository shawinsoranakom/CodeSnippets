def test_bad_request(self):
        request = self.request_factory.get("/")
        response = bad_request(request, Exception())
        self.assertContains(response, b"<h1>Bad Request (400)</h1>", status_code=400)