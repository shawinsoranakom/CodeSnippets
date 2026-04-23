def test_non_printable_chars_in_file_names(self):
        file_name = "non-\x00printable\x00\n_chars.txt\x00"
        payload = client.FakePayload()
        payload.write(
            "\r\n".join(
                [
                    "--" + client.BOUNDARY,
                    f'Content-Disposition: form-data; name="file"; '
                    f'filename="{file_name}"',
                    "Content-Type: application/octet-stream",
                    "",
                    "You got pwnd.\r\n",
                ]
            )
        )
        payload.write("\r\n--" + client.BOUNDARY + "--\r\n")
        r = {
            "CONTENT_LENGTH": len(payload),
            "CONTENT_TYPE": client.MULTIPART_CONTENT,
            "PATH_INFO": "/echo/",
            "REQUEST_METHOD": "POST",
            "wsgi.input": payload,
        }
        response = self.client.request(**r)
        # Non-printable chars are sanitized.
        received = response.json()
        self.assertEqual(received["file"], "non-printable_chars.txt")