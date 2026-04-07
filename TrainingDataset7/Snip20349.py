def test_coalesce_workaround_mysql(self):
        past = datetime(1900, 1, 1)
        now = timezone.now()
        Article.objects.create(title="Testing with Django", written=now)
        past_sql = RawSQL("cast(%s as datetime)", (past,))
        articles = Article.objects.annotate(
            last_updated=Greatest(
                Coalesce("written", past_sql),
                Coalesce("published", past_sql),
            ),
        )
        self.assertEqual(articles.first().last_updated, now)