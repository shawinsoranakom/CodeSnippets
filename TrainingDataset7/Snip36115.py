def test_unsupported_values_from_callable_returned_unmodified(self):
        for value in self.invalid_iterable + self.invalid_nested:
            with self.subTest(value=value):
                self.assertEqual(normalize_choices(lambda: value), value)