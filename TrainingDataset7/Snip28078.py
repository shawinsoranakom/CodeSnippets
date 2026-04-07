def test_none_key_and_exact_lookup(self):
        self.assertSequenceEqual(
            NullableJSONModel.objects.filter(value__a="b", value__j=None),
            [self.objs[4]],
        )