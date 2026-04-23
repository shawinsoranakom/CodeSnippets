def test_ineq(a, b, expected, *, strict=True):
            greater = (sympy.Gt, is_gt) if strict else (sympy.Ge, is_ge)
            less = (sympy.Lt, is_lt) if strict else (sympy.Le, is_le)

            if isinstance(expected, bool):
                # expected is always True
                for fn in greater:
                    self.assertEqual(fn(a, b), expected)
                    self.assertEqual(fn(b, a), not expected)
                for fn in less:
                    self.assertEqual(fn(b, a), expected)
                    self.assertEqual(fn(a, b), not expected)
            else:
                for fn in greater:
                    with self.assertRaisesRegex(ValueError, expected):
                        fn(a, b)
                for fn in less:
                    with self.assertRaisesRegex(ValueError, expected):
                        fn(b, a)