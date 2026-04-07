def test_in(self):
        self.assertSequenceEqual(
            Article.objects.exclude(id__in=[]),
            [self.a5, self.a6, self.a4, self.a2, self.a3, self.a7, self.a1],
        )