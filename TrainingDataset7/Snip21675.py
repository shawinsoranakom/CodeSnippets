def test_filter_count(self):
        with CaptureQueriesContext(connection) as ctx:
            self.assertEqual(
                Employee.objects.annotate(
                    department_salary_rank=Window(
                        Rank(), partition_by="department", order_by="-salary"
                    )
                )
                .filter(department_salary_rank=1)
                .count(),
                5,
            )
        self.assertEqual(len(ctx.captured_queries), 1)
        sql = ctx.captured_queries[0]["sql"].lower()
        self.assertEqual(sql.count("select"), 3)
        self.assertNotIn("group by", sql)