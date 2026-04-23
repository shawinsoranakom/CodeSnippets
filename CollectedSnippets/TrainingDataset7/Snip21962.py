def test_filename_overflow(self):
        """
        File names over 256 characters (dangerous on some platforms) get fixed
        up.
        """
        long_str = "f" * 300
        cases = [
            # field name, filename, expected
            ("long_filename", "%s.txt" % long_str, "%s.txt" % long_str[:251]),
            ("long_extension", "foo.%s" % long_str, ".%s" % long_str[:254]),
            ("no_extension", long_str, long_str[:255]),
            ("no_filename", ".%s" % long_str, ".%s" % long_str[:254]),
            ("long_everything", "%s.%s" % (long_str, long_str), ".%s" % long_str[:254]),
        ]
        payload = client.FakePayload()
        for name, filename, _ in cases:
            payload.write(
                "\r\n".join(
                    [
                        "--" + client.BOUNDARY,
                        'Content-Disposition: form-data; name="{}"; filename="{}"',
                        "Content-Type: application/octet-stream",
                        "",
                        "Oops.",
                        "",
                    ]
                ).format(name, filename)
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
        result = response.json()
        for name, _, expected in cases:
            got = result[name]
            self.assertEqual(expected, got, "Mismatch for {}".format(name))
            self.assertLess(
                len(got), 256, "Got a long file name (%s characters)." % len(got)
            )