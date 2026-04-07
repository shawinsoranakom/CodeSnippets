def test_assign_clear_related_set(self):
        # Use descriptor assignment to allocate ForeignKey. Null is legal, so
        # existing members of the set that are not in the assignment set are
        # set to null.
        self.r2.article_set.set([self.a2, self.a3])
        self.assertSequenceEqual(self.r2.article_set.all(), [self.a2, self.a3])
        # Clear the rest of the set
        self.r.article_set.clear()
        self.assertSequenceEqual(self.r.article_set.all(), [])
        self.assertSequenceEqual(
            Article.objects.filter(reporter__isnull=True),
            [self.a, self.a4],
        )