def test_all_null(self):
        Article.objects.create(title="Testing with Django", written=timezone.now())
        articles = Article.objects.annotate(first_updated=Least("published", "updated"))
        self.assertIsNone(articles.first().first_updated)