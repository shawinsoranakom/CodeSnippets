def test_optimizations(self):
        with CaptureQueriesContext(connection) as context:
            list(
                Experiment.objects.values(
                    exists=Exists(
                        Experiment.objects.order_by("pk"),
                    )
                ).order_by()
            )
        captured_queries = context.captured_queries
        self.assertEqual(len(captured_queries), 1)
        captured_sql = captured_queries[0]["sql"]
        self.assertNotIn(
            connection.ops.quote_name(Experiment._meta.pk.column),
            captured_sql,
        )
        self.assertIn(
            connection.ops.limit_offset_sql(None, 1),
            captured_sql,
        )
        self.assertNotIn("ORDER BY", captured_sql)