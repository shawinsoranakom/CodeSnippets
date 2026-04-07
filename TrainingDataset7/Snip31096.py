def test_base64_invalid_encoding(self):
        payload = FakePayload(
            "\r\n".join(
                [
                    f"--{BOUNDARY}",
                    'Content-Disposition: form-data; name="file"; filename="test.txt"',
                    "Content-Type: application/octet-stream",
                    "Content-Transfer-Encoding: base64",
                    "",
                    f"\r\nZsg£\r\n--{BOUNDARY}--",
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
        msg = "Could not decode base64 data."
        with self.assertRaisesMessage(MultiPartParserError, msg):
            request.POST