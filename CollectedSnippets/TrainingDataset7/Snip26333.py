def test_forward_assign_with_queryset(self):
        # Querysets used in m2m assignments are pre-evaluated so their value
        # isn't affected by the clearing operation in ManyRelatedManager.set()
        # (#19816).
        self.a1.publications.set([self.p1, self.p2])

        qs = self.a1.publications.filter(title="The Python Journal")
        self.a1.publications.set(qs)

        self.assertEqual(1, self.a1.publications.count())
        self.assertEqual(1, qs.count())