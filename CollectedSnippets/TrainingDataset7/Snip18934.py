def test_rich_lookup(self):
        # Django provides a rich database lookup API.
        self.assertEqual(Article.objects.get(id__exact=self.a.id), self.a)
        self.assertEqual(Article.objects.get(headline__startswith="Swallow"), self.a)
        self.assertEqual(Article.objects.get(pub_date__year=2005), self.a)
        self.assertEqual(
            Article.objects.get(pub_date__year=2005, pub_date__month=7), self.a
        )
        self.assertEqual(
            Article.objects.get(
                pub_date__year=2005, pub_date__month=7, pub_date__day=28
            ),
            self.a,
        )
        self.assertEqual(Article.objects.get(pub_date__week_day=5), self.a)