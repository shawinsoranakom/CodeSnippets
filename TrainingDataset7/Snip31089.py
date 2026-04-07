def test_POST_multipart_handler_parses_input(self):
        payload = FakePayload(
            "\r\n".join(
                [
                    f"--{BOUNDARY}",
                    'Content-Disposition: form-data; name="name"',
                    "",
                    "value",
                    f"--{BOUNDARY}--",
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
        self.assertEqual(request.POST, "_POST")
        self.assertEqual(request.FILES, "_FILES")