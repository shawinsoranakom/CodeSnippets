def test_add_obj(self):

        base_str = "<strong>strange</strong>"
        add_str = "hello</br>"

        class Add:
            def __add__(self, other):
                return base_str + other

        class AddSafe:
            def __add__(self, other):
                return mark_safe(base_str) + other

        class Radd:
            def __radd__(self, other):
                return other + base_str

        class RaddSafe:
            def __radd__(self, other):
                return other + mark_safe(base_str)

        left_add_expected = f"{base_str}{add_str}"
        right_add_expected = f"{add_str}{base_str}"
        cases = [
            # Left-add test cases.
            (Add(), add_str, left_add_expected, str),
            (Add(), mark_safe(add_str), left_add_expected, str),
            (AddSafe(), add_str, left_add_expected, str),
            (AddSafe(), mark_safe(add_str), left_add_expected, SafeString),
            # Right-add test cases.
            (add_str, Radd(), right_add_expected, str),
            (mark_safe(add_str), Radd(), right_add_expected, str),
            (add_str, Radd(), right_add_expected, str),
            (mark_safe(add_str), RaddSafe(), right_add_expected, SafeString),
        ]
        for lhs, rhs, expected, expected_type in cases:
            with self.subTest(lhs=lhs, rhs=rhs):
                result = lhs + rhs
                self.assertEqual(result, expected)
                self.assertEqual(type(result), expected_type)

        cases = [
            ("hello", Add()),
            ("hello", AddSafe()),
            (Radd(), "hello"),
            (RaddSafe(), "hello"),
        ]
        for lhs, rhs in cases:
            with self.subTest(lhs=lhs, rhs=rhs), self.assertRaises(TypeError):
                lhs + rhs