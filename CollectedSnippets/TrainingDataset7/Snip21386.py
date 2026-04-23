def test_aggregate_subquery_annotation(self):
        with self.assertNumQueries(1) as ctx:
            aggregate = Company.objects.annotate(
                ceo_salary=Subquery(
                    Employee.objects.filter(
                        id=OuterRef("ceo_id"),
                    ).values("salary")
                ),
            ).aggregate(
                ceo_salary_gt_20=Count("pk", filter=Q(ceo_salary__gt=20)),
            )
        self.assertEqual(aggregate, {"ceo_salary_gt_20": 1})
        # Aggregation over a subquery annotation doesn't annotate the subquery
        # twice in the inner query.
        sql = ctx.captured_queries[0]["sql"]
        self.assertLessEqual(sql.count("SELECT"), 3)
        # GROUP BY isn't required to aggregate over a query that doesn't
        # contain nested aggregates.
        self.assertNotIn("GROUP BY", sql)