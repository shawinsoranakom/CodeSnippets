def test_lookup_exclude_nonexistent_key(self):
        # Values without the key are ignored.
        condition = Q(value__foo="bax")
        objs_with_value = [self.objs[6]]
        objs_with_different_value = [self.objs[0], self.objs[7]]
        self.assertCountEqual(
            NullableJSONModel.objects.exclude(condition),
            objs_with_different_value,
        )
        self.assertSequenceEqual(
            NullableJSONModel.objects.exclude(~condition),
            objs_with_value,
        )
        self.assertCountEqual(
            NullableJSONModel.objects.filter(condition | ~condition),
            objs_with_value + objs_with_different_value,
        )
        self.assertCountEqual(
            NullableJSONModel.objects.exclude(condition & ~condition),
            objs_with_value + objs_with_different_value,
        )
        # Add the __isnull lookup to get an exhaustive set.
        self.assertCountEqual(
            NullableJSONModel.objects.exclude(condition & Q(value__foo__isnull=False)),
            self.objs[0:6] + self.objs[7:],
        )
        self.assertSequenceEqual(
            NullableJSONModel.objects.filter(condition & Q(value__foo__isnull=False)),
            objs_with_value,
        )