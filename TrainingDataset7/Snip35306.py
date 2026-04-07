def test_equal(self):
        valid_tests = (
            ("http://example.com/?", "http://example.com/"),
            ("http://example.com/?x=1&", "http://example.com/?x=1"),
            ("http://example.com/?x=1&y=2", "http://example.com/?y=2&x=1"),
            ("http://example.com/?x=1&y=2", "http://example.com/?y=2&x=1"),
            (
                "http://example.com/?x=1&y=2&a=1&a=2",
                "http://example.com/?a=1&a=2&y=2&x=1",
            ),
            ("/path/to/?x=1&y=2&z=3", "/path/to/?z=3&y=2&x=1"),
            ("?x=1&y=2&z=3", "?z=3&y=2&x=1"),
            ("/test_utils/no_template_used/", reverse_lazy("no_template_used")),
        )
        for url1, url2 in valid_tests:
            with self.subTest(url=url1):
                self.assertURLEqual(url1, url2)