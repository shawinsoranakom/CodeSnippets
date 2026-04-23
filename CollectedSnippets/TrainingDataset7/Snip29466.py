def test_default_argument(self):
        AggregateTestModel.objects.all().delete()
        tests = [
            (ArrayAgg("char_field", default=["<empty>"]), ["<empty>"]),
            (ArrayAgg("integer_field", default=[0]), [0]),
            (ArrayAgg("boolean_field", default=[False]), [False]),
            (BitAnd("integer_field", default=0), 0),
            (BitOr("integer_field", default=0), 0),
            (BoolAnd("boolean_field", default=False), False),
            (BoolOr("boolean_field", default=False), False),
            (JSONBAgg("integer_field", default=["<empty>"]), ["<empty>"]),
            (
                JSONBAgg("integer_field", default=Value(["<empty>"], JSONField())),
                ["<empty>"],
            ),
            (BitXor("integer_field", default=0), 0),
        ]
        for aggregation, expected_result in tests:
            with self.subTest(aggregation=aggregation):
                # Empty result with non-execution optimization.
                with self.assertNumQueries(0):
                    values = AggregateTestModel.objects.none().aggregate(
                        aggregation=aggregation,
                    )
                    self.assertEqual(values, {"aggregation": expected_result})
                # Empty result when query must be executed.
                with transaction.atomic(), self.assertNumQueries(1):
                    values = AggregateTestModel.objects.aggregate(
                        aggregation=aggregation,
                    )
                    self.assertEqual(values, {"aggregation": expected_result})