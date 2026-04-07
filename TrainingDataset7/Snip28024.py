def test_has_key_null_value(self):
        self.assertSequenceEqual(
            NullableJSONModel.objects.filter(value__has_key="j"),
            [self.objs[4]],
        )