def test_default_ordering(self):
        """
        By default, Article.objects.all() orders by pub_date descending, then
        headline ascending.
        """
        self.assertQuerySetEqual(
            Article.objects.all(),
            [
                "Article 4",
                "Article 2",
                "Article 3",
                "Article 1",
            ],
            attrgetter("headline"),
        )

        # Getting a single item should work too:
        self.assertEqual(Article.objects.all()[0], self.a4)