def test_reversed_ordering(self):
        """
        Ordering can be reversed using the reverse() method on a queryset.
        This allows you to extract things like "the last two items" (reverse
        and then take the first two).
        """
        self.assertQuerySetEqual(
            Article.objects.reverse()[:2],
            [
                "Article 1",
                "Article 3",
            ],
            attrgetter("headline"),
        )