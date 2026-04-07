def test_reverse_assign_with_queryset(self):
        # Querysets used in M2M assignments are pre-evaluated so their value
        # isn't affected by the clearing operation in ManyRelatedManager.set()
        # (#19816).
        self.p1.article_set.set([self.a1, self.a2])

        qs = self.p1.article_set.filter(
            headline="Django lets you build web apps easily"
        )
        self.p1.article_set.set(qs)

        self.assertEqual(1, self.p1.article_set.count())
        self.assertEqual(1, qs.count())