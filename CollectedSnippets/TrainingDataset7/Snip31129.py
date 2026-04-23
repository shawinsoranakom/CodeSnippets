def test_wsgi_request_headers_get(self):
        request = WSGIRequest(self.ENVIRON)
        self.assertEqual(request.headers.get("User-Agent"), "python-requests/1.2.0")
        self.assertEqual(request.headers.get("user-agent"), "python-requests/1.2.0")
        self.assertEqual(request.headers.get("Content-Type"), "text/html")
        self.assertEqual(request.headers.get("Content-Length"), "100")