def test_parsing_asctime_nonascii_digits(self):
        """Non-ASCII unicode decimals raise an error."""
        with self.assertRaises(ValueError):
            parse_http_date("Sun Nov  6 08:49:37 １９９４")
        with self.assertRaises(ValueError):
            parse_http_date("Sun Nov １２ 08:49:37 1994")