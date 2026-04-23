def test_invalid_inputs(self):
        cases = [
            # Non-numeric strings.
            None,
            [],
            {},
            object(),
            "abc123",
            "123abc",
            "foo",
            "error",
            "¿Cómo esta usted?",
            # Scientific notation - missing exponent value.
            "1e",
            "1e+",
            "1e-",
            # Scientific notation - missing base number.
            "e400",
            "e+400",
            "e-400",
            # Scientific notation - invalid exponent value.
            "1e^2",
            "1e2e3",
            "1e2a",
            "1e2.0",
            "1e2,0",
            # Scientific notation - misplaced decimal point.
            "1e.2",
            "1e2.",
            # Scientific notation - misplaced '+' sign.
            "1+e2",
            "1e2+",
        ]
        for value in cases:
            with self.subTest(value=value):
                self.assertEqual(floatformat(value), "")
            with self.subTest(value=value, arg="bar"):
                self.assertEqual(floatformat(value, "bar"), "")