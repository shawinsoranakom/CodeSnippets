def test_empty_multipart_handled_gracefully(self):
        """
        If passed an empty multipart message, MultiPartParser will return
        an empty QueryDict.
        """
        r = {
            "CONTENT_LENGTH": 0,
            "CONTENT_TYPE": client.MULTIPART_CONTENT,
            "PATH_INFO": "/echo/",
            "REQUEST_METHOD": "POST",
            "wsgi.input": client.FakePayload(b""),
        }
        self.assertEqual(self.client.request(**r).json(), {})