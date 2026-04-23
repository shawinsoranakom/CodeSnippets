def test_urls(self):
        self.assertEqual(
            urlize("http://google.com"),
            '<a href="http://google.com" rel="nofollow">http://google.com</a>',
        )
        self.assertEqual(
            urlize("http://google.com/"),
            '<a href="http://google.com/" rel="nofollow">http://google.com/</a>',
        )
        self.assertEqual(
            urlize("www.google.com"),
            '<a href="https://www.google.com" rel="nofollow">www.google.com</a>',
        )
        self.assertEqual(
            urlize("djangoproject.org"),
            '<a href="https://djangoproject.org" rel="nofollow">djangoproject.org</a>',
        )
        self.assertEqual(
            urlize("djangoproject.org/"),
            '<a href="https://djangoproject.org/" rel="nofollow">'
            "djangoproject.org/</a>",
        )