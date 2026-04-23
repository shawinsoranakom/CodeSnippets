def test_clear(self):
        # Relation sets can be cleared:
        self.p2.article_set.clear()
        self.assertSequenceEqual(self.p2.article_set.all(), [])
        self.assertSequenceEqual(self.a4.publications.all(), [])

        # And you can clear from the other end
        self.p2.article_set.add(self.a3, self.a4)
        self.assertSequenceEqual(
            self.p2.article_set.all(),
            [self.a3, self.a4],
        )
        self.assertSequenceEqual(self.a4.publications.all(), [self.p2])
        self.a4.publications.clear()
        self.assertSequenceEqual(self.a4.publications.all(), [])
        self.assertSequenceEqual(self.p2.article_set.all(), [self.a3])