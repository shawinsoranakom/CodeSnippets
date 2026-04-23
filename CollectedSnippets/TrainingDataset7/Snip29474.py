def test_array_agg_jsonfield_order_by(self):
        values = AggregateTestModel.objects.aggregate(
            arrayagg=ArrayAgg(
                KeyTransform("lang", "json_field"),
                filter=Q(json_field__lang__isnull=False),
                order_by=KeyTransform("lang", "json_field"),
            ),
        )
        self.assertEqual(values, {"arrayagg": ["en", "pl"]})