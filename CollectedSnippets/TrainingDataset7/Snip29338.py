def test_order_by_override(self):
        """
        Only the last order_by has any effect (since they each override any
        previous ordering).
        """
        self.assertQuerySetEqual(
            Article.objects.order_by("id"),
            [
                "Article 1",
                "Article 2",
                "Article 3",
                "Article 4",
            ],
            attrgetter("headline"),
        )
        self.assertQuerySetEqual(
            Article.objects.order_by("id").order_by("-headline"),
            [
                "Article 4",
                "Article 3",
                "Article 2",
                "Article 1",
            ],
            attrgetter("headline"),
        )