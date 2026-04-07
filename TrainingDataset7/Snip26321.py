def test_related_sets(self):
        # Article objects have access to their related Publication objects.
        self.assertSequenceEqual(self.a1.publications.all(), [self.p1])
        self.assertSequenceEqual(
            self.a2.publications.all(),
            [self.p4, self.p2, self.p3, self.p1],
        )
        # Publication objects have access to their related Article objects.
        self.assertSequenceEqual(
            self.p2.article_set.all(),
            [self.a3, self.a2, self.a4],
        )
        self.assertSequenceEqual(
            self.p1.article_set.all(),
            [self.a1, self.a2],
        )
        self.assertSequenceEqual(
            Publication.objects.get(id=self.p4.id).article_set.all(),
            [self.a2],
        )