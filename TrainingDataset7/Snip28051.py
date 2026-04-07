def test_deep_negative_lookup_array(self):
        self.assertSequenceEqual(
            NullableJSONModel.objects.filter(**{"value__-1__0": 2}),
            [self.objs[5]],
        )