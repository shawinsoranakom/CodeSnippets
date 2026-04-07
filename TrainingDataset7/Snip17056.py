def test_unreferenced_aggregate_annotation_pruned(self):
        with CaptureQueriesContext(connection) as ctx:
            cnt = Book.objects.annotate(
                authors_count=Count("authors"),
            ).count()
        self.assertEqual(cnt, 2)
        sql = ctx.captured_queries[0]["sql"].lower()
        self.assertEqual(sql.count("select"), 2, "Subquery wrapping required")
        self.assertNotIn("authors_count", sql)