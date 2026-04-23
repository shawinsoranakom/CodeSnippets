def test_shallow_list_negative_lookup(self):
        self.assertSequenceEqual(
            NullableJSONModel.objects.filter(**{"value__-2": 1}), [self.objs[5]]
        )