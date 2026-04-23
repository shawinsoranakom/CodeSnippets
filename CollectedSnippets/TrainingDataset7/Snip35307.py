def test_not_equal(self):
        invalid_tests = (
            # Protocol must be the same.
            ("http://example.com/", "https://example.com/"),
            ("http://example.com/?x=1&x=2", "https://example.com/?x=2&x=1"),
            ("http://example.com/?x=1&y=bar&x=2", "https://example.com/?y=bar&x=2&x=1"),
            # Parameters of the same name must be in the same order.
            ("/path/to?a=1&a=2", "/path/to/?a=2&a=1"),
        )
        for url1, url2 in invalid_tests:
            with self.subTest(url=url1), self.assertRaises(AssertionError):
                self.assertURLEqual(url1, url2)