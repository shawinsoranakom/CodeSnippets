def test_refresh_for_update(self):
        a = Article.objects.create(pub_date=datetime.now())
        for_update_sql = connection.ops.for_update_sql()

        with transaction.atomic(), CaptureQueriesContext(connection) as ctx:
            a.refresh_from_db(from_queryset=Article.objects.select_for_update())
        self.assertTrue(
            any(for_update_sql in query["sql"] for query in ctx.captured_queries)
        )