def test_wsgi_request_headers_getitem(self):
        request = WSGIRequest(self.ENVIRON)
        self.assertEqual(request.headers["User-Agent"], "python-requests/1.2.0")
        self.assertEqual(request.headers["user-agent"], "python-requests/1.2.0")
        self.assertEqual(request.headers["user_agent"], "python-requests/1.2.0")
        self.assertEqual(request.headers["Content-Type"], "text/html")
        self.assertEqual(request.headers["Content-Length"], "100")