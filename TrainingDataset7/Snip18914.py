def test_extra_method_select_argument_with_dashes_and_values(self):
        # The 'select' argument to extra() supports names with dashes in
        # them, as long as you use values().
        Article.objects.bulk_create(
            [
                Article(
                    headline="Article 10", pub_date=datetime(2005, 7, 31, 12, 30, 45)
                ),
                Article(headline="Article 11", pub_date=datetime(2008, 1, 1)),
                Article(
                    headline="Article 12",
                    pub_date=datetime(2008, 12, 31, 23, 59, 59, 999999),
                ),
            ]
        )
        dicts = (
            Article.objects.filter(pub_date__year=2008)
            .extra(select={"dashed-value": "1"})
            .values("headline", "dashed-value")
        )
        self.assertEqual(
            [sorted(d.items()) for d in dicts],
            [
                [("dashed-value", 1), ("headline", "Article 11")],
                [("dashed-value", 1), ("headline", "Article 12")],
            ],
        )