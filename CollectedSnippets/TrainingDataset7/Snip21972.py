def test_upload_header_fields_too_large(self):
        payload = client.FakePayload(
            "\r\n".join(
                [
                    "--" + client.BOUNDARY,
                    'Content-Disposition: form-data; name="my_file"; '
                    'filename="test.txt"',
                    "Content-Type: text/plain",
                    "X-Long-Header: %s" % ("-" * (MAX_TOTAL_HEADER_SIZE + 1)),
                    "",
                    "file contents",
                    "--" + client.BOUNDARY + "--\r\n",
                ]
            ),
        )
        r = {
            "CONTENT_LENGTH": len(payload),
            "CONTENT_TYPE": client.MULTIPART_CONTENT,
            "PATH_INFO": "/echo_content/",
            "REQUEST_METHOD": "POST",
            "wsgi.input": payload,
        }
        response = self.client.request(**r)
        self.assertEqual(response.status_code, 400)