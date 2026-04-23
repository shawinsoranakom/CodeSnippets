def test_order_by_nulls_last(self):
        Article.objects.filter(headline="Article 3").update(author=self.author_1)
        Article.objects.filter(headline="Article 4").update(author=self.author_2)
        # asc and desc are chainable with nulls_last.
        self.assertQuerySetEqualReversible(
            Article.objects.order_by(F("author").desc(nulls_last=True), "headline"),
            [self.a4, self.a3, self.a1, self.a2],
        )
        self.assertQuerySetEqualReversible(
            Article.objects.order_by(F("author").asc(nulls_last=True), "headline"),
            [self.a3, self.a4, self.a1, self.a2],
        )
        self.assertQuerySetEqualReversible(
            Article.objects.order_by(
                Upper("author__name").desc(nulls_last=True), "headline"
            ),
            [self.a4, self.a3, self.a1, self.a2],
        )
        self.assertQuerySetEqualReversible(
            Article.objects.order_by(
                Upper("author__name").asc(nulls_last=True), "headline"
            ),
            [self.a3, self.a4, self.a1, self.a2],
        )
        self.assertQuerySetEqualReversible(
            Article.objects.annotate(upper_name=Upper("author__name")).order_by(
                F("upper_name").asc(nulls_last=True), "headline"
            ),
            [self.a3, self.a4, self.a1, self.a2],
        )