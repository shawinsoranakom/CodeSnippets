def test_array_agg_integerfield_order_by(self):
        values = AggregateTestModel.objects.aggregate(
            arrayagg=ArrayAgg("integer_field", order_by=F("integer_field").desc())
        )
        self.assertEqual(values, {"arrayagg": [2, 1, 0, 0]})