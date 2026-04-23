def test_referenced_aggregate_annotation_kept(self):
        with CaptureQueriesContext(connection) as ctx:
            Book.objects.annotate(
                authors_count=Count("authors"),
            ).aggregate(Avg("authors_count"))
        sql = ctx.captured_queries[0]["sql"].lower()
        self.assertEqual(sql.count("select"), 2, "Subquery wrapping required")
        self.assertEqual(sql.count("authors_count"), 2)