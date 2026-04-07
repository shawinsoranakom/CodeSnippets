def test_add_after_prefetch(self):
        a4 = Article.objects.prefetch_related("publications").get(id=self.a4.id)
        self.assertEqual(a4.publications.count(), 1)
        a4.publications.add(self.p1)
        self.assertEqual(a4.publications.count(), 2)