def test_POST_after_body_read_and_stream_read(self):
        """
        POST should be populated even if body is read first, and then
        the stream is read second.
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
        self.assertEqual(request.read(1), b"n")
        self.assertEqual(request.POST, {"name": ["value"]})