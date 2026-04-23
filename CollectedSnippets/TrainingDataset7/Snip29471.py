def test_array_agg_booleanfield(self):
        values = AggregateTestModel.objects.aggregate(
            arrayagg=ArrayAgg("boolean_field")
        )
        self.assertEqual(values, {"arrayagg": [True, False, False, True]})