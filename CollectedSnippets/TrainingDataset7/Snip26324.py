def test_delete(self):
        # If we delete a Publication, its Articles won't be able to access it.
        self.p1.delete()
        self.assertSequenceEqual(
            Publication.objects.all(),
            [self.p4, self.p2, self.p3],
        )
        self.assertSequenceEqual(self.a1.publications.all(), [])
        # If we delete an Article, its Publications won't be able to access it.
        self.a2.delete()
        self.assertSequenceEqual(
            Article.objects.all(),
            [self.a1, self.a3, self.a4],
        )
        self.assertSequenceEqual(
            self.p2.article_set.all(),
            [self.a3, self.a4],
        )