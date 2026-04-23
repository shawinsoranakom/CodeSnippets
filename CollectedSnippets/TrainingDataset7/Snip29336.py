def test_default_ordering_override(self):
        """
        Override ordering with order_by, which is in the same format as the
        ordering attribute in models.
        """
        self.assertQuerySetEqual(
            Article.objects.order_by("headline"),
            [
                "Article 1",
                "Article 2",
                "Article 3",
                "Article 4",
            ],
            attrgetter("headline"),
        )
        self.assertQuerySetEqual(
            Article.objects.order_by("pub_date", "-headline"),
            [
                "Article 1",
                "Article 3",
                "Article 2",
                "Article 4",
            ],
            attrgetter("headline"),
        )