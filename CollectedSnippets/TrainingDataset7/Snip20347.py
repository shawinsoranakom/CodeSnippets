def test_propagates_null(self):
        Article.objects.create(title="Testing with Django", written=timezone.now())
        articles = Article.objects.annotate(
            last_updated=Greatest("written", "published")
        )
        self.assertIsNone(articles.first().last_updated)