def test_assign_with_queryset(self):
        # Querysets used in reverse FK assignments are pre-evaluated
        # so their value isn't affected by the clearing operation in
        # RelatedManager.set() (#19816).
        self.r2.article_set.set([self.a2, self.a3])

        qs = self.r2.article_set.filter(headline="Second")
        self.r2.article_set.set(qs)

        self.assertEqual(1, self.r2.article_set.count())
        self.assertEqual(1, qs.count())