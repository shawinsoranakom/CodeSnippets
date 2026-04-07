def setUp(self):
        payload = FakePayload("a=1&a=2&a=3\r\n")
        self.request = WSGIRequest(
            {
                "REQUEST_METHOD": "POST",
                "CONTENT_TYPE": "application/x-www-form-urlencoded",
                "CONTENT_LENGTH": len(payload),
                "wsgi.input": payload,
            }
        )