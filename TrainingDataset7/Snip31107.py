def test_multipart_with_header_fields_too_large(self):
        payload = FakePayload(
            "\r\n".join(
                [
                    "--boundary",
                    'Content-Disposition: form-data; name="name"',
                    "X-Long-Header: %s" % ("-" * (MAX_TOTAL_HEADER_SIZE + 1)),
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
                "CONTENT_LENGTH": len(payload),
                "wsgi.input": payload,
            }
        )
        msg = "Request max total header size exceeded."
        with self.assertRaisesMessage(MultiPartParserError, msg):
            request.POST