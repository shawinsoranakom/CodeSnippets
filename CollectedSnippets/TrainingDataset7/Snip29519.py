def test_default_argument(self):
        StatTestModel.objects.all().delete()
        tests = [
            (Corr(y="int2", x="int1", default=0), 0),
            (CovarPop(y="int2", x="int1", default=0), 0),
            (CovarPop(y="int2", x="int1", sample=True, default=0), 0),
            (RegrAvgX(y="int2", x="int1", default=0), 0),
            (RegrAvgY(y="int2", x="int1", default=0), 0),
            # RegrCount() doesn't support the default argument.
            (RegrIntercept(y="int2", x="int1", default=0), 0),
            (RegrR2(y="int2", x="int1", default=0), 0),
            (RegrSlope(y="int2", x="int1", default=0), 0),
            (RegrSXX(y="int2", x="int1", default=0), 0),
            (RegrSXY(y="int2", x="int1", default=0), 0),
            (RegrSYY(y="int2", x="int1", default=0), 0),
        ]
        for aggregation, expected_result in tests:
            with self.subTest(aggregation=aggregation):
                # Empty result with non-execution optimization.
                with self.assertNumQueries(0):
                    values = StatTestModel.objects.none().aggregate(
                        aggregation=aggregation,
                    )
                    self.assertEqual(values, {"aggregation": expected_result})
                # Empty result when query must be executed.
                with self.assertNumQueries(1):
                    values = StatTestModel.objects.aggregate(
                        aggregation=aggregation,
                    )
                    self.assertEqual(values, {"aggregation": expected_result})