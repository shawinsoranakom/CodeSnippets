def test_idn(self):
        """
        #13704 - Check urlize handles IDN correctly
        """
        # The "✶" below is \N{SIX POINTED BLACK STAR}, not "*" \N{ASTERISK}.
        self.assertEqual(
            urlize("http://c✶.ws"),
            '<a href="http://c%E2%9C%B6.ws" rel="nofollow">http://c✶.ws</a>',
        )
        self.assertEqual(
            urlize("www.c✶.ws"),
            '<a href="https://www.c%E2%9C%B6.ws" rel="nofollow">www.c✶.ws</a>',
        )
        self.assertEqual(
            urlize("c✶.org"),
            '<a href="https://c%E2%9C%B6.org" rel="nofollow">c✶.org</a>',
        )
        self.assertEqual(
            urlize("info@c✶.org"),
            '<a href="mailto:info@c%E2%9C%B6.org">info@c✶.org</a>',
        )

        # Pre-encoded IDNA is urlized but not re-encoded.
        self.assertEqual(
            urlize("www.xn--iny-zx5a.com/idna2003"),
            '<a href="https://www.xn--iny-zx5a.com/idna2003"'
            ' rel="nofollow">www.xn--iny-zx5a.com/idna2003</a>',
        )
        self.assertEqual(
            urlize("www.xn--fa-hia.com/idna2008"),
            '<a href="https://www.xn--fa-hia.com/idna2008"'
            ' rel="nofollow">www.xn--fa-hia.com/idna2008</a>',
        )