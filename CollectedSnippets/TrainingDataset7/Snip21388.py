def test_aggregate_rawsql_annotation(self):
        with self.assertNumQueries(1) as ctx:
            aggregate = Company.objects.annotate(
                salary=RawSQL("SUM(num_chairs) OVER (ORDER BY num_employees)", []),
            ).aggregate(
                count=Count("pk"),
            )
            self.assertEqual(aggregate, {"count": 3})
        sql = ctx.captured_queries[0]["sql"]
        self.assertNotIn("GROUP BY", sql)