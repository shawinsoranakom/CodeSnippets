def test_extra_ordering(self):
        """
        Ordering can be based on fields included from an 'extra' clause
        """
        self.assertQuerySetEqual(
            Article.objects.extra(
                select={"foo": "pub_date"}, order_by=["foo", "headline"]
            ),
            [
                "Article 1",
                "Article 2",
                "Article 3",
                "Article 4",
            ],
            attrgetter("headline"),
        )