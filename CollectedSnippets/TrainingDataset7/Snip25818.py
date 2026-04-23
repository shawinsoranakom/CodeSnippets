def test_escaping(self):
        # Underscores, percent signs and backslashes have special meaning in
        # the underlying SQL code, but Django handles the quoting of them
        # automatically.
        a8 = Article.objects.create(
            headline="Article_ with underscore", pub_date=datetime(2005, 11, 20)
        )

        self.assertSequenceEqual(
            Article.objects.filter(headline__startswith="Article"),
            [a8, self.a5, self.a6, self.a4, self.a2, self.a3, self.a7, self.a1],
        )
        self.assertSequenceEqual(
            Article.objects.filter(headline__startswith="Article_"),
            [a8],
        )
        a9 = Article.objects.create(
            headline="Article% with percent sign", pub_date=datetime(2005, 11, 21)
        )
        self.assertSequenceEqual(
            Article.objects.filter(headline__startswith="Article"),
            [a9, a8, self.a5, self.a6, self.a4, self.a2, self.a3, self.a7, self.a1],
        )
        self.assertSequenceEqual(
            Article.objects.filter(headline__startswith="Article%"),
            [a9],
        )
        a10 = Article.objects.create(
            headline="Article with \\ backslash", pub_date=datetime(2005, 11, 22)
        )
        self.assertSequenceEqual(
            Article.objects.filter(headline__contains="\\"),
            [a10],
        )