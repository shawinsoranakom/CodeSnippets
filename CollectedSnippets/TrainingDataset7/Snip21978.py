def test_filename_traversal_upload(self):
        os.makedirs(UPLOAD_TO, exist_ok=True)
        tests = [
            "..&#x2F;test.txt",
            "..&sol;test.txt",
        ]
        for file_name in tests:
            with self.subTest(file_name=file_name):
                payload = client.FakePayload()
                payload.write(
                    "\r\n".join(
                        [
                            "--" + client.BOUNDARY,
                            'Content-Disposition: form-data; name="my_file"; '
                            'filename="%s";' % file_name,
                            "Content-Type: text/plain",
                            "",
                            "file contents.\r\n",
                            "\r\n--" + client.BOUNDARY + "--\r\n",
                        ]
                    ),
                )
                r = {
                    "CONTENT_LENGTH": len(payload),
                    "CONTENT_TYPE": client.MULTIPART_CONTENT,
                    "PATH_INFO": "/upload_traversal/",
                    "REQUEST_METHOD": "POST",
                    "wsgi.input": payload,
                }
                response = self.client.request(**r)
                result = response.json()
                self.assertEqual(response.status_code, 200)
                self.assertEqual(result["file_name"], "test.txt")
                self.assertIs(
                    os.path.exists(os.path.join(MEDIA_ROOT, "test.txt")),
                    False,
                )
                self.assertIs(
                    os.path.exists(os.path.join(UPLOAD_TO, "test.txt")),
                    True,
                )