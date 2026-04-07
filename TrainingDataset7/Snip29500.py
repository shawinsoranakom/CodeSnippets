def test_jsonb_agg_jsonfield_order_by(self):
        values = AggregateTestModel.objects.aggregate(
            jsonbagg=JSONBAgg(
                KeyTransform("lang", "json_field"),
                filter=Q(json_field__lang__isnull=False),
                order_by=KeyTransform("lang", "json_field"),
            ),
        )
        self.assertEqual(values, {"jsonbagg": ["en", "pl"]})