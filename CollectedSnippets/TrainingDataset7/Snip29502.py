def test_array_agg_order_by_in_subquery(self):
        stats = []
        for i, agg in enumerate(AggregateTestModel.objects.order_by("char_field")):
            stats.append(StatTestModel(related_field=agg, int1=i, int2=i + 1))
            stats.append(StatTestModel(related_field=agg, int1=i + 1, int2=i))
        StatTestModel.objects.bulk_create(stats)

        aggregate = ArrayAgg("stattestmodel__int1", order_by="-stattestmodel__int2")
        expected_result = [
            ("Foo1", [0, 1]),
            ("Foo2", [1, 2]),
            ("Foo3", [2, 3]),
            ("Foo4", [3, 4]),
        ]

        subquery = (
            AggregateTestModel.objects.filter(
                pk=OuterRef("pk"),
            )
            .annotate(agg=aggregate)
            .values("agg")
        )
        values = (
            AggregateTestModel.objects.annotate(
                agg=Subquery(subquery),
            )
            .order_by("char_field")
            .values_list("char_field", "agg")
        )
        self.assertEqual(list(values), expected_result)