def test_create_after_prefetch(self):
        a4 = Article.objects.prefetch_related("publications").get(id=self.a4.id)
        self.assertSequenceEqual(a4.publications.all(), [self.p2])
        p5 = a4.publications.create(title="Django beats")
        self.assertCountEqual(a4.publications.all(), [self.p2, p5])