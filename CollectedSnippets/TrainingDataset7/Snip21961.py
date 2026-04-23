def test_dangerous_file_names(self):
        """
        Uploaded file names should be sanitized before ever reaching the view.
        """
        # This test simulates possible directory traversal attacks by a
        # malicious uploader We have to do some monkeybusiness here to
        # construct a malicious payload with an invalid file name (containing
        # os.sep or os.pardir). This similar to what an attacker would need to
        # do when trying such an attack.
        payload = client.FakePayload()
        for i, name in enumerate(CANDIDATE_TRAVERSAL_FILE_NAMES):
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
        # The filenames should have been sanitized by the time it got to the
        # view.
        received = response.json()
        for i, name in enumerate(CANDIDATE_TRAVERSAL_FILE_NAMES):
            got = received["file%s" % i]
            self.assertEqual(got, "hax0rd.txt")