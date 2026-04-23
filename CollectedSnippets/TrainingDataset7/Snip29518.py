def test_empty_result_set(self):
        StatTestModel.objects.all().delete()
        tests = [
            (Corr(y="int2", x="int1"), None),
            (CovarPop(y="int2", x="int1"), None),
            (CovarPop(y="int2", x="int1", sample=True), None),
            (RegrAvgX(y="int2", x="int1"), None),
            (RegrAvgY(y="int2", x="int1"), None),
            (RegrCount(y="int2", x="int1"), 0),
            (RegrIntercept(y="int2", x="int1"), None),
            (RegrR2(y="int2", x="int1"), None),
            (RegrSlope(y="int2", x="int1"), None),
            (RegrSXX(y="int2", x="int1"), None),
            (RegrSXY(y="int2", x="int1"), None),
            (RegrSYY(y="int2", x="int1"), None),
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