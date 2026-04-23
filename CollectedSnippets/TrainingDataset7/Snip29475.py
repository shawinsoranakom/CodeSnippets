def test_array_agg_filter_and_order_by_params(self):
        values = AggregateTestModel.objects.aggregate(
            arrayagg=ArrayAgg(
                "char_field",
                filter=Q(json_field__has_key="lang"),
                order_by=LPad(Cast("integer_field", CharField()), 2, Value("0")),
            )
        )
        self.assertEqual(values, {"arrayagg": ["Foo2", "Foo4"]})