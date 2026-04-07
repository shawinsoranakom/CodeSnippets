def test_created_without_related(self):
        self.assertIsNone(self.a3.reporter)
        # Need to reget a3 to refresh the cache
        a3 = Article.objects.get(pk=self.a3.pk)
        with self.assertRaises(AttributeError):
            getattr(a3.reporter, "id")
        # Accessing an article's 'reporter' attribute returns None
        # if the reporter is set to None.
        self.assertIsNone(a3.reporter)
        # To retrieve the articles with no reporters set, use
        # "reporter__isnull=True".
        self.assertSequenceEqual(
            Article.objects.filter(reporter__isnull=True), [self.a3]
        )
        # We can achieve the same thing by filtering for the case where the
        # reporter is None.
        self.assertSequenceEqual(Article.objects.filter(reporter=None), [self.a3])
        # Set the reporter for the Third article
        self.assertSequenceEqual(self.r.article_set.all(), [self.a, self.a2])
        self.r.article_set.add(a3)
        self.assertSequenceEqual(
            self.r.article_set.all(),
            [self.a, self.a2, self.a3],
        )
        # Remove an article from the set, and check that it was removed.
        self.r.article_set.remove(a3)
        self.assertSequenceEqual(self.r.article_set.all(), [self.a, self.a2])
        self.assertSequenceEqual(
            Article.objects.filter(reporter__isnull=True), [self.a3]
        )