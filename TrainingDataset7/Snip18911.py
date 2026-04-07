def test_year_lookup_edge_case(self):
        # Edge-case test: A year lookup should retrieve all objects in
        # the given year, including Jan. 1 and Dec. 31.
        a11 = Article.objects.create(
            headline="Article 11",
            pub_date=datetime(2008, 1, 1),
        )
        a12 = Article.objects.create(
            headline="Article 12",
            pub_date=datetime(2008, 12, 31, 23, 59, 59, 999999),
        )
        self.assertSequenceEqual(
            Article.objects.filter(pub_date__year=2008),
            [a11, a12],
        )