def test_default_ordering_does_not_affect_group_by(self):
        Article.objects.exclude(headline="Article 4").update(author=self.author_1)
        Article.objects.filter(headline="Article 4").update(author=self.author_2)
        articles = Article.objects.values("author").annotate(count=Count("author"))
        self.assertCountEqual(
            articles,
            [
                {"author": self.author_1.pk, "count": 3},
                {"author": self.author_2.pk, "count": 1},
            ],
        )