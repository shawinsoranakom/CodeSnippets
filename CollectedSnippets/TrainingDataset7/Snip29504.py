def test_ordering_isnt_cleared_for_array_subquery(self):
        inner_qs = AggregateTestModel.objects.order_by("-integer_field")
        qs = AggregateTestModel.objects.annotate(
            integers=Func(
                Subquery(inner_qs.values("integer_field")),
                function="ARRAY",
                output_field=ArrayField(base_field=IntegerField()),
            ),
        )
        self.assertSequenceEqual(
            qs.first().integers,
            inner_qs.values_list("integer_field", flat=True),
        )