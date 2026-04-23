def test_jsonb_agg_integerfield_order_by(self):
        values = AggregateTestModel.objects.aggregate(
            jsonbagg=JSONBAgg("integer_field", order_by=F("integer_field").desc()),
        )
        self.assertEqual(values, {"jsonbagg": [2, 1, 0, 0]})