def test_m2m_table(self):
        self.assertSequenceEqual(
            self.article.authors.order_by("last_name"),
            [self.a2, self.a1],
        )
        self.assertSequenceEqual(self.a1.article_set.all(), [self.article])
        self.assertSequenceEqual(
            self.article.authors.filter(last_name="Jones"),
            [self.a2],
        )