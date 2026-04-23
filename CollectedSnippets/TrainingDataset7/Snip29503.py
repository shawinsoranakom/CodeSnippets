def test_string_agg_array_agg_filter_in_subquery(self):
        StatTestModel.objects.bulk_create(
            [
                StatTestModel(related_field=self.aggs[0], int1=0, int2=5),
                StatTestModel(related_field=self.aggs[0], int1=1, int2=4),
                StatTestModel(related_field=self.aggs[0], int1=2, int2=3),
            ]
        )

        aggregate = ArrayAgg(
            "stattestmodel__int1",
            filter=Q(stattestmodel__int2__gt=3),
        )
        expected_result = [("Foo1", [0, 1]), ("Foo2", None)]

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
            .filter(
                char_field__in=["Foo1", "Foo2"],
            )
            .order_by("char_field")
            .values_list("char_field", "agg")
        )
        self.assertEqual(list(values), expected_result)