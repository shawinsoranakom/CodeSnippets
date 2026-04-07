def test_array_agg_charfield_order_by(self):
        order_by_test_cases = (
            (F("char_field").desc(), ["Foo4", "Foo3", "Foo2", "Foo1"]),
            (F("char_field").asc(), ["Foo1", "Foo2", "Foo3", "Foo4"]),
            (F("char_field"), ["Foo1", "Foo2", "Foo3", "Foo4"]),
            (
                [F("boolean_field"), F("char_field").desc()],
                ["Foo4", "Foo2", "Foo3", "Foo1"],
            ),
            (
                (F("boolean_field"), F("char_field").desc()),
                ["Foo4", "Foo2", "Foo3", "Foo1"],
            ),
            ("char_field", ["Foo1", "Foo2", "Foo3", "Foo4"]),
            ("-char_field", ["Foo4", "Foo3", "Foo2", "Foo1"]),
            (Concat("char_field", Value("@")), ["Foo1", "Foo2", "Foo3", "Foo4"]),
            (Concat("char_field", Value("@")).desc(), ["Foo4", "Foo3", "Foo2", "Foo1"]),
            (
                (
                    Substr("char_field", 1, 1),
                    F("integer_field"),
                    Substr("char_field", 4, 1).desc(),
                ),
                ["Foo3", "Foo1", "Foo2", "Foo4"],
            ),
        )
        for order_by, expected_output in order_by_test_cases:
            with self.subTest(order_by=order_by, expected_output=expected_output):
                values = AggregateTestModel.objects.aggregate(
                    arrayagg=ArrayAgg("char_field", order_by=order_by)
                )
                self.assertEqual(values, {"arrayagg": expected_output})