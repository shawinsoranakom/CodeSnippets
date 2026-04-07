def test_prefetch_related_no_queries_optimization_disabled(self):
        qs = Article.objects.prefetch_related("publications")
        article = qs.get()
        with self.assertNumQueries(0):
            article.publications.count()
        with self.assertNumQueries(0):
            article.publications.exists()