def test_unicode_file_name_rfc2231(self):
        """
        Receiving file upload when filename is encoded with RFC 2231.
        """
        payload = client.FakePayload()
        payload.write(
            "\r\n".join(
                [
                    "--" + client.BOUNDARY,
                    'Content-Disposition: form-data; name="file_unicode"; '
                    "filename*=UTF-8''%s" % quote(UNICODE_FILENAME),
                    "Content-Type: application/octet-stream",
                    "",
                    "You got pwnd.\r\n",
                    "\r\n--" + client.BOUNDARY + "--\r\n",
                ]
            )
        )

        r = {
            "CONTENT_LENGTH": len(payload),
            "CONTENT_TYPE": client.MULTIPART_CONTENT,
            "PATH_INFO": "/unicode_name/",
            "REQUEST_METHOD": "POST",
            "wsgi.input": payload,
        }
        response = self.client.request(**r)
        self.assertEqual(response.status_code, 200)