def test_ignores_null(self):
        now = timezone.now()
        Article.objects.create(title="Testing with Django", written=now)
        articles = Article.objects.annotate(
            last_updated=Greatest("written", "published")
        )
        self.assertEqual(articles.first().last_updated, now)