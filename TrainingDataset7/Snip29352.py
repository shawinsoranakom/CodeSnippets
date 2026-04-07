def test_extra_ordering_quoting(self):
        """
        If the extra clause uses an SQL keyword for a name, it will be
        protected by quoting.
        """
        self.assertQuerySetEqual(
            Article.objects.extra(
                select={"order": "pub_date"}, order_by=["order", "headline"]
            ),
            [
                "Article 1",
                "Article 2",
                "Article 3",
                "Article 4",
            ],
            attrgetter("headline"),
        )