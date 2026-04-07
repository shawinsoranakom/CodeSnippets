def test_cookie_edgecases(self):
        # Cookies that RFC 6265 allows.
        self.assertEqual(
            parse_cookie("a=b; Domain=example.com"), {"a": "b", "Domain": "example.com"}
        )
        # parse_cookie() has historically kept only the last cookie with the
        # same name.
        self.assertEqual(parse_cookie("a=b; h=i; a=c"), {"a": "c", "h": "i"})