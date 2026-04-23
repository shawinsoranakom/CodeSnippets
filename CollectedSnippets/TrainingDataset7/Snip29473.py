def test_array_agg_jsonfield(self):
        values = AggregateTestModel.objects.aggregate(
            arrayagg=ArrayAgg(
                KeyTransform("lang", "json_field"),
                filter=Q(json_field__lang__isnull=False),
            ),
        )
        self.assertEqual(values, {"arrayagg": ["pl", "en"]})