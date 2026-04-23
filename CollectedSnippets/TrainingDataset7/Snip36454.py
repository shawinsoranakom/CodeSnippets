def test_rfc2231_parsing(self):
        test_data = (
            (
                "Content-Type: application/x-stuff; "
                "title*=us-ascii'en-us'This%20is%20%2A%2A%2Afun%2A%2A%2A",
                "This is ***fun***",
            ),
            (
                "Content-Type: application/x-stuff; title*=UTF-8''foo-%c3%a4.html",
                "foo-ä.html",
            ),
            (
                "Content-Type: application/x-stuff; title*=iso-8859-1''foo-%E4.html",
                "foo-ä.html",
            ),
        )
        for raw_line, expected_title in test_data:
            parsed = parse_header_parameters(raw_line)
            self.assertEqual(parsed[1]["title"], expected_title)