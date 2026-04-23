def setUp(self):
        payload = FakePayload("\r\n".join(["a=1&a=2&a=3", ""]))
        self.request = WSGIRequest(
            {
                "REQUEST_METHOD": "POST",
                "CONTENT_TYPE": "application/x-www-form-urlencoded",
                "CONTENT_LENGTH": len(payload),
                "wsgi.input": payload,
            }
        )