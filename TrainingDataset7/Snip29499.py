def test_jsonb_agg_booleanfield_order_by(self):
        order_by_test_cases = (
            (F("boolean_field").asc(), [False, False, True, True]),
            (F("boolean_field").desc(), [True, True, False, False]),
            (F("boolean_field"), [False, False, True, True]),
        )
        for order_by, expected_output in order_by_test_cases:
            with self.subTest(order_by=order_by, expected_output=expected_output):
                values = AggregateTestModel.objects.aggregate(
                    jsonbagg=JSONBAgg("boolean_field", order_by=order_by),
                )
                self.assertEqual(values, {"jsonbagg": expected_output})