def test_basic(self):
        now = timezone.now()
        before = now - timedelta(hours=1)
        Article.objects.create(
            title="Testing with Django", written=before, published=now
        )
        articles = Article.objects.annotate(
            last_updated=Greatest("written", "published")
        )
        self.assertEqual(articles.first().last_updated, now)