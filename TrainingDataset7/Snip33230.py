def test_ipv6(self):
        self.assertEqual(
            urlize("http://[2001:db8:cafe::2]/api/9"),
            '<a href="http://[2001:db8:cafe::2]/api/9" rel="nofollow">'
            "http://[2001:db8:cafe::2]/api/9</a>",
        )