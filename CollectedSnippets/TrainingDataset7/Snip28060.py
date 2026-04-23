def test_array_key_contains(self):
        tests = [
            ([], [self.objs[7]]),
            ("bar", [self.objs[7]]),
            (["bar"], [self.objs[7]]),
            ("ar", []),
        ]
        for value, expected in tests:
            with self.subTest(value=value):
                self.assertSequenceEqual(
                    NullableJSONModel.objects.filter(value__bar__contains=value),
                    expected,
                )