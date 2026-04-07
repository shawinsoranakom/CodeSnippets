def test_ignores_null(self):
        now = timezone.now()
        Article.objects.create(title="Testing with Django", written=now)
        articles = Article.objects.annotate(
            first_updated=Least("written", "published"),
        )
        self.assertEqual(articles.first().first_updated, now)