def test_array_agg_integerfield(self):
        values = AggregateTestModel.objects.aggregate(
            arrayagg=ArrayAgg("integer_field")
        )
        self.assertEqual(values, {"arrayagg": [0, 1, 2, 0]})