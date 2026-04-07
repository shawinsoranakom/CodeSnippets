def test_rfc2231_wrong_title(self):
        """
        Test wrongly formatted RFC 2231 headers (missing double single quotes).
        Parsing should not crash (#24209).
        """
        test_data = (
            (
                "Content-Type: application/x-stuff; "
                "title*='This%20is%20%2A%2A%2Afun%2A%2A%2A",
                "'This%20is%20%2A%2A%2Afun%2A%2A%2A",
            ),
            ("Content-Type: application/x-stuff; title*='foo.html", "'foo.html"),
            ("Content-Type: application/x-stuff; title*=bar.html", "bar.html"),
        )
        for raw_line, expected_title in test_data:
            parsed = parse_header_parameters(raw_line)
            self.assertEqual(parsed[1]["title"], expected_title)