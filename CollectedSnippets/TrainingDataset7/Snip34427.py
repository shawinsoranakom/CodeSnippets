def test_filter_numeric_argument_parsing(self):
        p = Parser("", builtins=[filter_library])

        # Values that resolve to a numeric literal.
        cases = {
            "5": 5,
            "-5": -5,
            "5.2": 5.2,
            ".4": 0.4,
            "5.2e3": 5200.0,  # 5.2 × 10³ = 5200.0.
            "5.2E3": 5200.0,  # Case-insensitive.
            "5.2e-3": 0.0052,  # Negative exponent.
            "-1.5E4": -15000.0,
            "+3.0e2": 300.0,
            ".5e2": 50.0,  # 0.5 × 10² = 50.0
        }
        for num, expected in cases.items():
            with self.subTest(num=num):
                self.assertEqual(FilterExpression(num, p).resolve({}), expected)
                self.assertEqual(
                    FilterExpression(f"0|default:{num}", p).resolve({}), expected
                )

        # Values that are interpreted as names of variables that do not exist.
        invalid_numbers = [
            "abc123",
            "123abc",
            "foo",
            "error",
            "1e",
            "e400",
            "1e.2",
            "1e2.",
            "1e2.0",
            "1e2a",
            "1e2e3",
        ]

        for num in invalid_numbers:
            with self.subTest(num=num):
                self.assertIsNone(
                    FilterExpression(num, p).resolve({}, ignore_failures=True)
                )
                with self.assertRaises(VariableDoesNotExist):
                    FilterExpression(f"0|default:{num}", p).resolve({})

        # Values that are interpreted as an invalid variable name.
        invalid_numbers_and_var_names = [
            "1e-",
            "1e-a",
            "1+1",
            "1-1",
        ]
        for num in invalid_numbers_and_var_names:
            with self.subTest(num=num):
                with self.assertRaises(TemplateSyntaxError):
                    FilterExpression(num, p).resolve({})
                with self.assertRaises(TemplateSyntaxError):
                    FilterExpression(f"0|default:{num}", p).resolve({})