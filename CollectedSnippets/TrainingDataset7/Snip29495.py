def test_orderable_agg_alternative_fields(self):
        values = AggregateTestModel.objects.aggregate(
            arrayagg=ArrayAgg("integer_field", order_by=F("char_field").asc())
        )
        self.assertEqual(values, {"arrayagg": [0, 1, 0, 2]})