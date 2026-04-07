def test_set(self):
        # Use manager.set() to allocate ForeignKey. Null is legal, so existing
        # members of the set that are not in the assignment set are set to
        # null.
        self.r2.article_set.set([self.a2, self.a3])
        self.assertSequenceEqual(self.r2.article_set.all(), [self.a2, self.a3])
        # Use manager.set(clear=True)
        self.r2.article_set.set([self.a3, self.a4], clear=True)
        self.assertSequenceEqual(self.r2.article_set.all(), [self.a4, self.a3])
        # Clear the rest of the set
        self.r2.article_set.set([])
        self.assertSequenceEqual(self.r2.article_set.all(), [])
        self.assertSequenceEqual(
            Article.objects.filter(reporter__isnull=True),
            [self.a4, self.a2, self.a3],
        )