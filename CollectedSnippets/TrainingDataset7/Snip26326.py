def test_remove(self):
        # Removing publication from an article:
        self.assertSequenceEqual(
            self.p2.article_set.all(),
            [self.a3, self.a2, self.a4],
        )
        self.a4.publications.remove(self.p2)
        self.assertSequenceEqual(
            self.p2.article_set.all(),
            [self.a3, self.a2],
        )
        self.assertSequenceEqual(self.a4.publications.all(), [])
        # And from the other end
        self.p2.article_set.remove(self.a3)
        self.assertSequenceEqual(self.p2.article_set.all(), [self.a2])
        self.assertSequenceEqual(self.a3.publications.all(), [])