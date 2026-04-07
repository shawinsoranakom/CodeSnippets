def setUp(self):
        self.request = WSGIRequest(
            {
                "REQUEST_METHOD": "GET",
                "wsgi.input": BytesIO(b""),
                "CONTENT_LENGTH": 3,
            }
        )