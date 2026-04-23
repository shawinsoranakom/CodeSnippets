def test_float_numbers(self):
        tests = [
            (9e-10, 10, "0.0000000009"),
            (9e-19, 2, "0.00"),
            (0.00000000000099, 0, "0"),
            (0.00000000000099, 13, "0.0000000000009"),
            (1e16, None, "10000000000000000"),
            (1e16, 2, "10000000000000000.00"),
            # A float without a fractional part (3.) results in a ".0" when no
            # decimal_pos is given. Contrast that with the Decimal('3.') case
            # in test_decimal_numbers which doesn't return a fractional part.
            (3.0, None, "3.0"),
        ]
        for value, decimal_pos, expected_value in tests:
            with self.subTest(value=value, decimal_pos=decimal_pos):
                self.assertEqual(nformat(value, ".", decimal_pos), expected_value)
        # Thousand grouping behavior.
        self.assertEqual(
            nformat(1e16, ".", thousand_sep=",", grouping=3, force_grouping=True),
            "10,000,000,000,000,000",
        )
        self.assertEqual(
            nformat(
                1e16,
                ".",
                decimal_pos=2,
                thousand_sep=",",
                grouping=3,
                force_grouping=True,
            ),
            "10,000,000,000,000,000.00",
        )