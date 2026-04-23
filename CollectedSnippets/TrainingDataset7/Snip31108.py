def test_POST_connection_error(self):
        """
        If wsgi.input.read() raises an exception while trying to read() the
        POST, the exception is identifiable (not a generic OSError).
        """

        class ExplodingBytesIO(BytesIO):
            def read(self, size=-1, /):
                raise OSError("kaboom!")

        payload = b"name=value"
        request = WSGIRequest(
            {
                "REQUEST_METHOD": "POST",
                "CONTENT_TYPE": "application/x-www-form-urlencoded",
                "CONTENT_LENGTH": len(payload),
                "wsgi.input": ExplodingBytesIO(payload),
            }
        )
        with self.assertRaises(UnreadablePostError):
            request.body