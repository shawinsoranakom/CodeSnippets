def test_unsupported_values_from_iterator_returned_unmodified(self):
        for value in self.invalid_nested:
            with self.subTest(value=value):
                self.assertEqual(
                    normalize_choices((lambda: (yield from value))()),
                    value,
                )