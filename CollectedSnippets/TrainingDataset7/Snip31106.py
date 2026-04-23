def test_multipart_non_ascii_content_type(self):
        request = WSGIRequest(
            {
                "REQUEST_METHOD": "POST",
                "CONTENT_TYPE": "multipart/form-data; boundary = \xe0",
                "CONTENT_LENGTH": 0,
                "wsgi.input": FakePayload(),
            }
        )
        msg = (
            "Invalid non-ASCII Content-Type in multipart: multipart/form-data; "
            "boundary = à"
        )
        with self.assertRaisesMessage(MultiPartParserError, msg):
            request.POST