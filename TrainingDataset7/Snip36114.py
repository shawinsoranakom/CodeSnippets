def test_unsupported_values_returned_unmodified(self):
        # Unsupported values must be returned unmodified for model system check
        # to work correctly.
        for value in self.invalid + self.invalid_iterable + self.invalid_nested:
            with self.subTest(value=value):
                self.assertEqual(normalize_choices(value), value)