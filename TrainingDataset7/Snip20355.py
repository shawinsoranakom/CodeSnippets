def test_basic(self):
        now = timezone.now()
        before = now - timedelta(hours=1)
        Article.objects.create(
            title="Testing with Django", written=before, published=now
        )
        articles = Article.objects.annotate(first_updated=Least("written", "published"))
        self.assertEqual(articles.first().first_updated, before)