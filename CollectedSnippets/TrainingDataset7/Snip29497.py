def test_jsonb_agg_charfield_order_by(self):
        order_by_test_cases = (
            (F("char_field").desc(), ["Foo4", "Foo3", "Foo2", "Foo1"]),
            (F("char_field").asc(), ["Foo1", "Foo2", "Foo3", "Foo4"]),
            (F("char_field"), ["Foo1", "Foo2", "Foo3", "Foo4"]),
            ("char_field", ["Foo1", "Foo2", "Foo3", "Foo4"]),
            ("-char_field", ["Foo4", "Foo3", "Foo2", "Foo1"]),
            (Concat("char_field", Value("@")), ["Foo1", "Foo2", "Foo3", "Foo4"]),
            (Concat("char_field", Value("@")).desc(), ["Foo4", "Foo3", "Foo2", "Foo1"]),
        )
        for order_by, expected_output in order_by_test_cases:
            with self.subTest(order_by=order_by, expected_output=expected_output):
                values = AggregateTestModel.objects.aggregate(
                    jsonbagg=JSONBAgg("char_field", order_by=order_by),
                )
                self.assertEqual(values, {"jsonbagg": expected_output})