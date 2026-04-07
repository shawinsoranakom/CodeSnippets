def test_request_path_begins_with_two_slashes(self):
        # //// creates a request with a path beginning with //
        request = self.factory.get("////absolute-uri")
        tests = (
            # location isn't provided
            (None, "http://testserver//absolute-uri"),
            # An absolute URL
            ("http://example.com/?foo=bar", "http://example.com/?foo=bar"),
            # A schema-relative URL
            ("//example.com/?foo=bar", "http://example.com/?foo=bar"),
            # Relative URLs
            ("/foo/bar/", "http://testserver/foo/bar/"),
            ("/foo/./bar/", "http://testserver/foo/bar/"),
            ("/foo/../bar/", "http://testserver/bar/"),
            ("///foo/bar/", "http://testserver/foo/bar/"),
        )
        for location, expected_url in tests:
            with self.subTest(location=location):
                self.assertEqual(
                    request.build_absolute_uri(location=location), expected_url
                )