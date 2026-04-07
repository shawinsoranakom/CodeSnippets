def test_deep_lookup_objs(self):
        self.assertSequenceEqual(
            NullableJSONModel.objects.filter(value__k__l="m"),
            [self.objs[4]],
        )