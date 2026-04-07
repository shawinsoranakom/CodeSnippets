def test_chain_date_time_lookups(self):
        self.assertCountEqual(
            Article.objects.filter(pub_date__month__gt=7),
            [self.a5, self.a6],
        )
        self.assertCountEqual(
            Article.objects.filter(pub_date__day__gte=27),
            [self.a2, self.a3, self.a4, self.a7],
        )
        self.assertCountEqual(
            Article.objects.filter(pub_date__hour__lt=8),
            [self.a1, self.a2, self.a3, self.a4, self.a7],
        )
        self.assertCountEqual(
            Article.objects.filter(pub_date__minute__lte=0),
            [self.a1, self.a2, self.a3, self.a4, self.a5, self.a6, self.a7],
        )