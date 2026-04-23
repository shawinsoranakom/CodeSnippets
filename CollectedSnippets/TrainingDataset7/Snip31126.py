def test_base_request_headers(self):
        request = HttpRequest()
        request.META = self.ENVIRON
        self.assertEqual(
            dict(request.headers),
            {
                "Content-Type": "text/html",
                "Content-Length": "100",
                "Accept": "*",
                "Host": "example.com",
                "User-Agent": "python-requests/1.2.0",
            },
        )