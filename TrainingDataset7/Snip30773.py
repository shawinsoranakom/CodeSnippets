def test_can_combine_queries_using_and_and_or_operators(self):
        s1 = Article.objects.filter(name__exact="Article 1")
        s2 = Article.objects.filter(name__exact="Article 2")
        self.assertSequenceEqual(
            (s1 | s2).order_by("name"),
            [self.articles[0], self.articles[1]],
        )
        self.assertSequenceEqual(s1 & s2, [])