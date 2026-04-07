def test_deep_lookup_array(self):
        self.assertSequenceEqual(
            NullableJSONModel.objects.filter(value__1__0=2),
            [self.objs[5]],
        )