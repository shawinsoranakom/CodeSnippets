def test_values_list(self):
        tests = [ArrayAgg("integer_field"), JSONBAgg("integer_field")]
        for aggregation in tests:
            with self.subTest(aggregation=aggregation):
                results = AggregateTestModel.objects.annotate(
                    agg=aggregation
                ).values_list("agg")
                self.assertCountEqual(
                    results,
                    [([0],), ([1],), ([2],), ([0],)],
                )