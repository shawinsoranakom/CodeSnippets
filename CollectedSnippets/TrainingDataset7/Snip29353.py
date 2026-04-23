def test_extra_ordering_with_table_name(self):
        self.assertQuerySetEqual(
            Article.objects.extra(order_by=["ordering_article.headline"]),
            [
                "Article 1",
                "Article 2",
                "Article 3",
                "Article 4",
            ],
            attrgetter("headline"),
        )
        self.assertQuerySetEqual(
            Article.objects.extra(order_by=["-ordering_article.headline"]),
            [
                "Article 4",
                "Article 3",
                "Article 2",
                "Article 1",
            ],
            attrgetter("headline"),
        )