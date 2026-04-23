def test_exact_sliced_queryset_limit_one(self):
        self.assertCountEqual(
            Article.objects.filter(author=Author.objects.all()[:1]),
            [self.a1, self.a2, self.a3, self.a4],
        )