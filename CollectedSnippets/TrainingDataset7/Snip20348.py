def test_coalesce_workaround(self):
        past = datetime(1900, 1, 1)
        now = timezone.now()
        Article.objects.create(title="Testing with Django", written=now)
        articles = Article.objects.annotate(
            last_updated=Greatest(
                Coalesce("written", past),
                Coalesce("published", past),
            ),
        )
        self.assertEqual(articles.first().last_updated, now)