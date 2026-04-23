def test_all_null(self):
        Article.objects.create(title="Testing with Django", written=timezone.now())
        articles = Article.objects.annotate(
            last_updated=Greatest("published", "updated")
        )
        self.assertIsNone(articles.first().last_updated)