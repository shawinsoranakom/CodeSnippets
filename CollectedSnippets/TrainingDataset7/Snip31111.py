def test_FILES_connection_error(self):
        """
        If wsgi.input.read() raises an exception while trying to read() the
        FILES, the exception is identifiable (not a generic OSError).
        """

        class ExplodingBytesIO(BytesIO):
            def read(self, size=-1, /):
                raise OSError("kaboom!")

        payload = b"x"
        request = WSGIRequest(
            {
                "REQUEST_METHOD": "POST",
                "CONTENT_TYPE": "multipart/form-data; boundary=foo_",
                "CONTENT_LENGTH": len(payload),
                "wsgi.input": ExplodingBytesIO(payload),
            }
        )
        with self.assertRaises(UnreadablePostError):
            request.FILES