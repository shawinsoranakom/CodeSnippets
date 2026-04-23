def test_coalesce_workaround(self):
        future = datetime(2100, 1, 1)
        now = timezone.now()
        Article.objects.create(title="Testing with Django", written=now)
        articles = Article.objects.annotate(
            last_updated=Least(
                Coalesce("written", future),
                Coalesce("published", future),
            ),
        )
        self.assertEqual(articles.first().last_updated, now)