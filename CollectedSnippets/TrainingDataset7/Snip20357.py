def test_propagates_null(self):
        Article.objects.create(title="Testing with Django", written=timezone.now())
        articles = Article.objects.annotate(first_updated=Least("written", "published"))
        self.assertIsNone(articles.first().first_updated)