def test_blank_filenames(self):
        """
        Receiving file upload when filename is blank (before and after
        sanitization) should be okay.
        """
        filenames = [
            "",
            # Normalized by MultiPartParser.IE_sanitize().
            "C:\\Windows\\",
            # Normalized by os.path.basename().
            "/",
            "ends-with-slash/",
        ]
        payload = client.FakePayload()
        for i, name in enumerate(filenames):
            payload.write(
                "\r\n".join(
                    [
                        "--" + client.BOUNDARY,
                        'Content-Disposition: form-data; name="file%s"; filename="%s"'
                        % (i, name),
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
        self.assertEqual(response.status_code, 200)

        # Empty filenames should be ignored
        received = response.json()
        for i, name in enumerate(filenames):
            self.assertIsNone(received.get("file%s" % i))