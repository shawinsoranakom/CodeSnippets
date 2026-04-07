def test_urlencoded(self):
        self.assertEqual(
            urlize("www.mystore.com/30%OffCoupons!"),
            '<a href="https://www.mystore.com/30%25OffCoupons" rel="nofollow">'
            "www.mystore.com/30%OffCoupons</a>!",
        )
        self.assertEqual(
            urlize("https://en.wikipedia.org/wiki/Caf%C3%A9"),
            '<a href="https://en.wikipedia.org/wiki/Caf%C3%A9" rel="nofollow">'
            "https://en.wikipedia.org/wiki/Caf%C3%A9</a>",
        )