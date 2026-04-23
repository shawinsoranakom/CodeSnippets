def test_bulk_delete(self):
        # Bulk delete some Publications - references to deleted publications
        # should go
        Publication.objects.filter(title__startswith="Science").delete()
        self.assertSequenceEqual(
            Publication.objects.all(),
            [self.p4, self.p1],
        )
        self.assertSequenceEqual(
            Article.objects.all(),
            [self.a1, self.a3, self.a2, self.a4],
        )
        self.assertSequenceEqual(
            self.a2.publications.all(),
            [self.p4, self.p1],
        )

        # Bulk delete some articles - references to deleted objects should go
        q = Article.objects.filter(headline__startswith="Django")
        self.assertSequenceEqual(q, [self.a1])
        q.delete()
        # After the delete, the QuerySet cache needs to be cleared,
        # and the referenced objects should be gone
        self.assertSequenceEqual(q, [])
        self.assertSequenceEqual(self.p1.article_set.all(), [self.a2])