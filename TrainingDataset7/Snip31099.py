def test_POST_after_body_read(self):
        """
        POST should be populated even if body is read first
        """
        payload = FakePayload("name=value")
        request = WSGIRequest(
            {
                "REQUEST_METHOD": "POST",
                "CONTENT_TYPE": "application/x-www-form-urlencoded",
                "CONTENT_LENGTH": len(payload),
                "wsgi.input": payload,
            }
        )
        request.body  # evaluate
        self.assertEqual(request.POST, {"name": ["value"]})