def test_lazystring(self):
        prepend_www = lazy(lambda url: "www." + url, str)
        self.assertEqual(
            urlize(prepend_www("google.com")),
            '<a href="https://www.google.com" rel="nofollow">www.google.com</a>',
        )