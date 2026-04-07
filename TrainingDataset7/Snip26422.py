def test_add_efficiency(self):
        r = Reporter.objects.create()
        articles = []
        for _ in range(3):
            articles.append(Article.objects.create())
        with self.assertNumQueries(1):
            r.article_set.add(*articles)
        self.assertEqual(r.article_set.count(), 3)