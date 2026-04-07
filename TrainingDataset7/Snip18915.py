def test_extra_method_select_argument_with_dashes(self):
        # If you use 'select' with extra() and names containing dashes on a
        # query that's *not* a values() query, those extra 'select' values
        # will silently be ignored.
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
        articles = Article.objects.filter(pub_date__year=2008).extra(
            select={"dashed-value": "1", "undashedvalue": "2"}
        )
        self.assertEqual(articles[0].undashedvalue, 2)