def test_exact_sliced_queryset_limit_one_offset(self):
        self.assertCountEqual(
            Article.objects.filter(author=Author.objects.all()[1:2]),
            [self.a5, self.a6, self.a7],
        )