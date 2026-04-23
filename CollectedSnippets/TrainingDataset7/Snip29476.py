def test_array_agg_filter(self):
        values = AggregateTestModel.objects.aggregate(
            arrayagg=ArrayAgg("integer_field", filter=Q(integer_field__gt=0)),
        )
        self.assertEqual(values, {"arrayagg": [1, 2]})