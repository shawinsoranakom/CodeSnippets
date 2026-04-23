def test_wsgi_request_headers(self):
        request = WSGIRequest(self.ENVIRON)
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