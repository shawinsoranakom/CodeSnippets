def _test_base64_upload(self, content, encode=base64.b64encode):
        payload = client.FakePayload(
            "\r\n".join(
                [
                    "--" + client.BOUNDARY,
                    'Content-Disposition: form-data; name="file"; filename="test.txt"',
                    "Content-Type: application/octet-stream",
                    "Content-Transfer-Encoding: base64",
                    "",
                ]
            )
        )
        payload.write(b"\r\n" + encode(content.encode()) + b"\r\n")
        payload.write("--" + client.BOUNDARY + "--\r\n")
        r = {
            "CONTENT_LENGTH": len(payload),
            "CONTENT_TYPE": client.MULTIPART_CONTENT,
            "PATH_INFO": "/echo_content/",
            "REQUEST_METHOD": "POST",
            "wsgi.input": payload,
        }
        response = self.client.request(**r)
        self.assertEqual(response.json()["file"], content)