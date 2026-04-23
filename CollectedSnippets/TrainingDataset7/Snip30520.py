def test_exists_union(self):
        qs1 = Number.objects.filter(num__gte=5)
        qs2 = Number.objects.filter(num__lte=5)
        with CaptureQueriesContext(connection) as context:
            self.assertIs(qs1.union(qs2).exists(), True)
        captured_queries = context.captured_queries
        self.assertEqual(len(captured_queries), 1)
        captured_sql = captured_queries[0]["sql"]
        self.assertNotIn(
            connection.ops.quote_name(Number._meta.pk.column),
            captured_sql,
        )
        self.assertEqual(
            captured_sql.count(connection.ops.limit_offset_sql(None, 1)), 1
        )