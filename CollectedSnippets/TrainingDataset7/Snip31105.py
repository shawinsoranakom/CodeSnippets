def test_multipart_without_boundary(self):
        request = WSGIRequest(
            {
                "REQUEST_METHOD": "POST",
                "CONTENT_TYPE": "multipart/form-data;",
                "CONTENT_LENGTH": 0,
                "wsgi.input": FakePayload(),
            }
        )
        with self.assertRaisesMessage(
            MultiPartParserError, "Invalid boundary in multipart: None"
        ):
            request.POST