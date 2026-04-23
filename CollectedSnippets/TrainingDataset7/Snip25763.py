def test_iterator(self):
        # Each QuerySet gets iterator(), which is a generator that "lazily"
        # returns results using database-level iteration.
        self.assertIsInstance(Article.objects.iterator(), collections.abc.Iterator)

        self.assertQuerySetEqual(
            Article.objects.iterator(),
            [
                "Article 5",
                "Article 6",
                "Article 4",
                "Article 2",
                "Article 3",
                "Article 7",
                "Article 1",
            ],
            transform=attrgetter("headline"),
        )
        # iterator() can be used on any QuerySet.
        self.assertQuerySetEqual(
            Article.objects.filter(headline__endswith="4").iterator(),
            ["Article 4"],
            transform=attrgetter("headline"),
        )