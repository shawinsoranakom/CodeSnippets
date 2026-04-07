def test_set_encoding_clears_POST(self):
        payload = FakePayload(
            "\r\n".join(
                [
                    f"--{BOUNDARY}",
                    'Content-Disposition: form-data; name="name"',
                    "",
                    "Hello Günter",
                    f"--{BOUNDARY}--",
                    "",
                ]
            )
        )
        request = WSGIRequest(
            {
                "REQUEST_METHOD": "POST",
                "CONTENT_TYPE": MULTIPART_CONTENT,
                "CONTENT_LENGTH": len(payload),
                "wsgi.input": payload,
            }
        )
        self.assertEqual(request.POST, {"name": ["Hello Günter"]})
        request.encoding = "iso-8859-16"