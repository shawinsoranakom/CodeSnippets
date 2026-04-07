def test_deep_negative_lookup_mixed(self):
        self.assertSequenceEqual(
            NullableJSONModel.objects.filter(**{"value__d__-1__f": "g"}),
            [self.objs[4]],
        )