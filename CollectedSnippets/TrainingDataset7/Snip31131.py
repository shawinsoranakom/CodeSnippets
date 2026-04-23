def test_parse_header_name(self):
        tests = (
            ("PATH_INFO", None),
            ("HTTP_ACCEPT", "Accept"),
            ("HTTP_USER_AGENT", "User-Agent"),
            ("HTTP_X_FORWARDED_PROTO", "X-Forwarded-Proto"),
            ("CONTENT_TYPE", "Content-Type"),
            ("CONTENT_LENGTH", "Content-Length"),
        )
        for header, expected in tests:
            with self.subTest(header=header):
                self.assertEqual(HttpHeaders.parse_header_name(header), expected)