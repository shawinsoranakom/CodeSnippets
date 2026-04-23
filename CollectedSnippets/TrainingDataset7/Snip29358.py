def test_order_by_f_expression(self):
        self.assertQuerySetEqual(
            Article.objects.order_by(F("headline")),
            [
                "Article 1",
                "Article 2",
                "Article 3",
                "Article 4",
            ],
            attrgetter("headline"),
        )
        self.assertQuerySetEqual(
            Article.objects.order_by(F("headline").asc()),
            [
                "Article 1",
                "Article 2",
                "Article 3",
                "Article 4",
            ],
            attrgetter("headline"),
        )
        self.assertQuerySetEqual(
            Article.objects.order_by(F("headline").desc()),
            [
                "Article 4",
                "Article 3",
                "Article 2",
                "Article 1",
            ],
            attrgetter("headline"),
        )