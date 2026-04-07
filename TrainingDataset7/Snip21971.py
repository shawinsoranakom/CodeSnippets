def test_upload_large_header_fields(self):
        payload = client.FakePayload(
            "\r\n".join(
                [
                    "--" + client.BOUNDARY,
                    'Content-Disposition: form-data; name="my_file"; '
                    'filename="test.txt"',
                    "Content-Type: text/plain",
                    "X-Long-Header: %s" % ("-" * 500),
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
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"my_file": "file contents"})