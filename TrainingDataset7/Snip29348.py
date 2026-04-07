def test_reverse_ordering_pure(self):
        qs1 = Article.objects.order_by(F("headline").asc())
        qs2 = qs1.reverse()
        self.assertQuerySetEqual(
            qs2,
            [
                "Article 4",
                "Article 3",
                "Article 2",
                "Article 1",
            ],
            attrgetter("headline"),
        )
        self.assertQuerySetEqual(
            qs1,
            [
                "Article 1",
                "Article 2",
                "Article 3",
                "Article 4",
            ],
            attrgetter("headline"),
        )