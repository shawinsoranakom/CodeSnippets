def test_empty_in(self):
        # Passing "in" an empty list returns no results ...
        self.assertQuerySetEqual(Article.objects.filter(pk__in=[]), [])
        # ... but can return results if we OR it with another query.
        self.assertQuerySetEqual(
            Article.objects.filter(Q(pk__in=[]) | Q(headline__icontains="goodbye")),
            ["Goodbye", "Hello and goodbye"],
            attrgetter("headline"),
        )