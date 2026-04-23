def test_value_after_read(self):
        """
        Construction of POST or body is not allowed after reading
        from request.
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
        self.assertEqual(request.read(2), b"na")
        with self.assertRaises(RawPostDataException):
            request.body
        self.assertEqual(request.POST, {})