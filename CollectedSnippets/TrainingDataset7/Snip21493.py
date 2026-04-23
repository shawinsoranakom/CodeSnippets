def test_repr(self):
        tests = [
            (None, "Value(None)"),
            ("str", "Value('str')"),
            (True, "Value(True)"),
            (42, "Value(42)"),
            (
                datetime.datetime(2019, 5, 15),
                "Value(datetime.datetime(2019, 5, 15, 0, 0))",
            ),
            (Decimal("3.14"), "Value(Decimal('3.14'))"),
        ]
        for value, expected in tests:
            with self.subTest(value=value):
                self.assertEqual(repr(Value(value)), expected)