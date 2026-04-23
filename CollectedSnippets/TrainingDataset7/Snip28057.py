def test_lookup_exclude(self):
        tests = [
            (Q(value__a="b"), [self.objs[0]]),
            (Q(value__foo="bax"), [self.objs[0], self.objs[7]]),
        ]
        for condition, expected in tests:
            self.assertCountEqual(
                NullableJSONModel.objects.exclude(condition),
                expected,
            )
            self.assertCountEqual(
                NullableJSONModel.objects.filter(~condition),
                expected,
            )