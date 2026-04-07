def test_in_keeps_value_ordering(self):
        query = (
            Article.objects.filter(slug__in=["a%d" % i for i in range(1, 8)])
            .values("pk")
            .query
        )
        self.assertIn(" IN (a1, a2, a3, a4, a5, a6, a7) ", str(query))