def test_other_arg_queries(self):
        # Try some arg queries with operations other than filter.
        self.assertEqual(
            Article.objects.get(
                Q(headline__startswith="Hello"), Q(headline__contains="bye")
            ).headline,
            "Hello and goodbye",
        )

        self.assertEqual(
            Article.objects.filter(
                Q(headline__startswith="Hello") | Q(headline__contains="bye")
            ).count(),
            3,
        )

        self.assertSequenceEqual(
            Article.objects.filter(
                Q(headline__startswith="Hello"), Q(headline__contains="bye")
            ).values(),
            [
                {
                    "headline": "Hello and goodbye",
                    "id": self.a3,
                    "pub_date": datetime(2005, 11, 29),
                },
            ],
        )

        self.assertEqual(
            Article.objects.filter(Q(headline__startswith="Hello")).in_bulk(
                [self.a1, self.a2]
            ),
            {self.a1: Article.objects.get(pk=self.a1)},
        )