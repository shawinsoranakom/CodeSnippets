def test_decimal_numbers(self):
        self.assertEqual(nformat(Decimal("1234"), "."), "1234")
        self.assertEqual(nformat(Decimal("1234.2"), "."), "1234.2")
        self.assertEqual(nformat(Decimal("1234"), ".", decimal_pos=2), "1234.00")
        self.assertEqual(
            nformat(Decimal("1234"), ".", grouping=2, thousand_sep=","), "1234"
        )
        self.assertEqual(
            nformat(
                Decimal("1234"), ".", grouping=2, thousand_sep=",", force_grouping=True
            ),
            "12,34",
        )
        self.assertEqual(nformat(Decimal("-1234.33"), ".", decimal_pos=1), "-1234.3")
        self.assertEqual(
            nformat(Decimal("0.00000001"), ".", decimal_pos=8), "0.00000001"
        )
        self.assertEqual(nformat(Decimal("9e-19"), ".", decimal_pos=2), "0.00")
        self.assertEqual(nformat(Decimal(".00000000000099"), ".", decimal_pos=0), "0")
        self.assertEqual(
            nformat(
                Decimal("1e16"), ".", thousand_sep=",", grouping=3, force_grouping=True
            ),
            "10,000,000,000,000,000",
        )
        self.assertEqual(
            nformat(
                Decimal("1e16"),
                ".",
                decimal_pos=2,
                thousand_sep=",",
                grouping=3,
                force_grouping=True,
            ),
            "10,000,000,000,000,000.00",
        )
        self.assertEqual(nformat(Decimal("3."), "."), "3")
        self.assertEqual(nformat(Decimal("3.0"), "."), "3.0")
        # Very large & small numbers.
        tests = [
            ("9e9999", None, "9e+9999"),
            ("9e9999", 3, "9.000e+9999"),
            ("9e201", None, "9e+201"),
            ("9e200", None, "9e+200"),
            ("1.2345e999", 2, "1.23e+999"),
            ("9e-999", None, "9e-999"),
            ("1e-7", 8, "0.00000010"),
            ("1e-8", 8, "0.00000001"),
            ("1e-9", 8, "0.00000000"),
            ("1e-10", 8, "0.00000000"),
            ("1e-11", 8, "0.00000000"),
            ("1" + ("0" * 300), 3, "1.000e+300"),
            ("0.{}1234".format("0" * 299), 3, "0.000"),
        ]
        for value, decimal_pos, expected_value in tests:
            with self.subTest(value=value):
                self.assertEqual(
                    nformat(Decimal(value), ".", decimal_pos), expected_value
                )