def test_exclude(self):
        a8 = Article.objects.create(
            headline="Article_ with underscore", pub_date=datetime(2005, 11, 20)
        )
        a9 = Article.objects.create(
            headline="Article% with percent sign", pub_date=datetime(2005, 11, 21)
        )
        a10 = Article.objects.create(
            headline="Article with \\ backslash", pub_date=datetime(2005, 11, 22)
        )
        # exclude() is the opposite of filter() when doing lookups:
        self.assertSequenceEqual(
            Article.objects.filter(headline__contains="Article").exclude(
                headline__contains="with"
            ),
            [self.a5, self.a6, self.a4, self.a2, self.a3, self.a7, self.a1],
        )
        self.assertSequenceEqual(
            Article.objects.exclude(headline__startswith="Article_"),
            [a10, a9, self.a5, self.a6, self.a4, self.a2, self.a3, self.a7, self.a1],
        )
        self.assertSequenceEqual(
            Article.objects.exclude(headline="Article 7"),
            [a10, a9, a8, self.a5, self.a6, self.a4, self.a2, self.a3, self.a1],
        )