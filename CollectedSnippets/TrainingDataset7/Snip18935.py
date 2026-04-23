def test_equal_lookup(self):
        # The "__exact" lookup type can be omitted, as a shortcut.
        self.assertEqual(Article.objects.get(id=self.a.id), self.a)
        self.assertEqual(
            Article.objects.get(headline="Swallow programs in Python"), self.a
        )

        self.assertSequenceEqual(
            Article.objects.filter(pub_date__year=2005),
            [self.a],
        )
        self.assertSequenceEqual(
            Article.objects.filter(pub_date__year=2004),
            [],
        )
        self.assertSequenceEqual(
            Article.objects.filter(pub_date__year=2005, pub_date__month=7),
            [self.a],
        )

        self.assertSequenceEqual(
            Article.objects.filter(pub_date__week_day=5),
            [self.a],
        )
        self.assertSequenceEqual(
            Article.objects.filter(pub_date__week_day=6),
            [],
        )