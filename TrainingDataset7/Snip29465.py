def test_empty_result_set(self):
        AggregateTestModel.objects.all().delete()
        tests = [
            ArrayAgg("char_field"),
            ArrayAgg("integer_field"),
            ArrayAgg("boolean_field"),
            BitAnd("integer_field"),
            BitOr("integer_field"),
            BoolAnd("boolean_field"),
            BoolOr("boolean_field"),
            JSONBAgg("integer_field"),
            BitXor("integer_field"),
        ]
        for aggregation in tests:
            with self.subTest(aggregation=aggregation):
                # Empty result with non-execution optimization.
                with self.assertNumQueries(0):
                    values = AggregateTestModel.objects.none().aggregate(
                        aggregation=aggregation,
                    )
                    self.assertEqual(values, {"aggregation": None})
                # Empty result when query must be executed.
                with self.assertNumQueries(1):
                    values = AggregateTestModel.objects.aggregate(
                        aggregation=aggregation,
                    )
                    self.assertEqual(values, {"aggregation": None})