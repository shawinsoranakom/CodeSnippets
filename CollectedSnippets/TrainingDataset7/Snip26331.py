def test_assign(self):
        # Relation sets can be assigned using set().
        self.p2.article_set.set([self.a4, self.a3])
        self.assertSequenceEqual(
            self.p2.article_set.all(),
            [self.a3, self.a4],
        )
        self.assertSequenceEqual(self.a4.publications.all(), [self.p2])
        self.a4.publications.set([self.p3.id])
        self.assertSequenceEqual(self.p2.article_set.all(), [self.a3])
        self.assertSequenceEqual(self.a4.publications.all(), [self.p3])

        # An alternate to calling clear() is to set an empty set.
        self.p2.article_set.set([])
        self.assertSequenceEqual(self.p2.article_set.all(), [])
        self.a4.publications.set([])
        self.assertSequenceEqual(self.a4.publications.all(), [])