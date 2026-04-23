def test_remove_after_prefetch(self):
        a4 = Article.objects.prefetch_related("publications").get(id=self.a4.id)
        self.assertSequenceEqual(a4.publications.all(), [self.p2])
        a4.publications.remove(self.p2)
        self.assertSequenceEqual(a4.publications.all(), [])