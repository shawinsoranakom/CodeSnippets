def test_POST_multipart_with_content_length_zero(self):
        """
        Multipart POST requests with Content-Length >= 0 are valid and need to
        be handled.
        """
        # According to RFC 9110 Section 8.6 every POST with Content-Length >= 0
        # is a valid request, so ensure that we handle Content-Length == 0.
        payload = FakePayload(
            "\r\n".join(
                [
                    "--boundary",
                    'Content-Disposition: form-data; name="name"',
                    "",
                    "value",
                    "--boundary--",
                ]
            )
        )
        request = WSGIRequest(
            {
                "REQUEST_METHOD": "POST",
                "CONTENT_TYPE": "multipart/form-data; boundary=boundary",
                "CONTENT_LENGTH": 0,
                "wsgi.input": payload,
            }
        )
        self.assertEqual(request.POST, {})