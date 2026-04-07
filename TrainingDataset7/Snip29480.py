def test_array_agg_with_empty_filter_and_default_values(self):
        for filter_value in ([-1], []):
            for default_value in ([], Value([])):
                with self.subTest(filter=filter_value, default=default_value):
                    queryset = AggregateTestModel.objects.annotate(
                        test_array_agg=ArrayAgg(
                            "stattestmodel__int1",
                            filter=Q(pk__in=filter_value),
                            default=default_value,
                        )
                    )
                    self.assertSequenceEqual(
                        queryset.values_list("test_array_agg", flat=True),
                        [[], [], [], []],
                    )