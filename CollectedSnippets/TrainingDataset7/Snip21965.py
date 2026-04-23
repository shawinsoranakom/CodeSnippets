def test_truncated_multipart_handled_gracefully(self):
        """
        If passed an incomplete multipart message, MultiPartParser does not
        attempt to read beyond the end of the stream, and simply will handle
        the part that can be parsed gracefully.
        """
        payload_str = "\r\n".join(
            [
                "--" + client.BOUNDARY,
                'Content-Disposition: form-data; name="file"; filename="foo.txt"',
                "Content-Type: application/octet-stream",
                "",
                "file contents" "--" + client.BOUNDARY + "--",
                "",
            ]
        )
        payload = client.FakePayload(payload_str[:-10])
        r = {
            "CONTENT_LENGTH": len(payload),
            "CONTENT_TYPE": client.MULTIPART_CONTENT,
            "PATH_INFO": "/echo/",
            "REQUEST_METHOD": "POST",
            "wsgi.input": payload,
        }
        self.assertEqual(self.client.request(**r).json(), {})