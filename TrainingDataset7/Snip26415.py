def test_related_set(self):
        # Reporter objects have access to their related Article objects.
        self.assertSequenceEqual(self.r.article_set.all(), [self.a, self.a2])
        self.assertSequenceEqual(
            self.r.article_set.filter(headline__startswith="Fir"), [self.a]
        )
        self.assertEqual(self.r.article_set.count(), 2)