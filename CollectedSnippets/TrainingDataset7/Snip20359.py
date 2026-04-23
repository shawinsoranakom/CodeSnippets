def test_coalesce_workaround_mysql(self):
        future = datetime(2100, 1, 1)
        now = timezone.now()
        Article.objects.create(title="Testing with Django", written=now)
        future_sql = RawSQL("cast(%s as datetime)", (future,))
        articles = Article.objects.annotate(
            last_updated=Least(
                Coalesce("written", future_sql),
                Coalesce("published", future_sql),
            ),
        )
        self.assertEqual(articles.first().last_updated, now)