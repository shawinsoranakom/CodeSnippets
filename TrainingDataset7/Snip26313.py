def test_add_remove_set_by_pk(self):
        a5 = Article.objects.create(headline="Django lets you create web apps easily")
        a5.publications.add(self.p1.pk)
        self.assertSequenceEqual(a5.publications.all(), [self.p1])
        a5.publications.set([self.p2.pk])
        self.assertSequenceEqual(a5.publications.all(), [self.p2])
        a5.publications.remove(self.p2.pk)
        self.assertSequenceEqual(a5.publications.all(), [])