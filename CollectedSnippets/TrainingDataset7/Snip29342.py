def test_order_by_nulls_first(self):
        Article.objects.filter(headline="Article 3").update(author=self.author_1)
        Article.objects.filter(headline="Article 4").update(author=self.author_2)
        # asc and desc are chainable with nulls_first.
        self.assertQuerySetEqualReversible(
            Article.objects.order_by(F("author").asc(nulls_first=True), "headline"),
            [self.a1, self.a2, self.a3, self.a4],
        )
        self.assertQuerySetEqualReversible(
            Article.objects.order_by(F("author").desc(nulls_first=True), "headline"),
            [self.a1, self.a2, self.a4, self.a3],
        )
        self.assertQuerySetEqualReversible(
            Article.objects.order_by(
                Upper("author__name").asc(nulls_first=True), "headline"
            ),
            [self.a1, self.a2, self.a3, self.a4],
        )
        self.assertQuerySetEqualReversible(
            Article.objects.order_by(
                Upper("author__name").desc(nulls_first=True), "headline"
            ),
            [self.a1, self.a2, self.a4, self.a3],
        )
        self.assertQuerySetEqualReversible(
            Article.objects.annotate(upper_name=Upper("author__name")).order_by(
                F("upper_name").desc(nulls_first=True), "headline"
            ),
            [self.a1, self.a2, self.a4, self.a3],
        )