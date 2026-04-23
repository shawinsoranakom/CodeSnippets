def test_multipart_post_field_with_invalid_base64(self):
        payload = FakePayload(
            "\r\n".join(
                [
                    f"--{BOUNDARY}",
                    'Content-Disposition: form-data; name="name"',
                    "Content-Transfer-Encoding: base64",
                    "",
                    "123",
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
        request.body  # evaluate
        self.assertEqual(request.POST, {"name": ["123"]})