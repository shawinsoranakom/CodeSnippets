def test_in(self):
        tests = [
            ([[]], [self.objs[1]]),
            ([{}], [self.objs[2]]),
            ([{"a": "b", "c": 14}], [self.objs[3]]),
            ([[1, [2]]], [self.objs[5]]),
        ]
        for lookup_value, expected in tests:
            with self.subTest(value__in=lookup_value):
                self.assertCountEqual(
                    NullableJSONModel.objects.filter(value__in=lookup_value), expected
                )