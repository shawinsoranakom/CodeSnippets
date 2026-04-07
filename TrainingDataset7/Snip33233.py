def test_exclamation_marks(self):
        """
        #23715 - Check urlize correctly handles exclamation marks after TLDs
        or query string
        """
        self.assertEqual(
            urlize("Go to djangoproject.com! and enjoy."),
            'Go to <a href="https://djangoproject.com" rel="nofollow">djangoproject.com'
            "</a>! and enjoy.",
        )
        self.assertEqual(
            urlize("Search for google.com/?q=! and see."),
            'Search for <a href="https://google.com/?q=" rel="nofollow">google.com/?q='
            "</a>! and see.",
        )
        self.assertEqual(
            urlize("Search for google.com/?q=dj!`? and see."),
            'Search for <a href="https://google.com/?q=dj%21%60%3F" rel="nofollow">'
            "google.com/?q=dj!`?</a> and see.",
        )
        self.assertEqual(
            urlize("Search for google.com/?q=dj!`?! and see."),
            'Search for <a href="https://google.com/?q=dj%21%60%3F" rel="nofollow">'
            "google.com/?q=dj!`?</a>! and see.",
        )