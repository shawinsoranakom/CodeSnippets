def test_wsgirequest_copy(self):
        request = WSGIRequest({"REQUEST_METHOD": "get", "wsgi.input": BytesIO(b"")})
        request_copy = copy.copy(request)
        self.assertIs(request_copy.environ, request.environ)