def test_key_iexact_none(self):
        self.assertSequenceEqual(
            NullableJSONModel.objects.filter(value__j__iexact=None),
            [self.objs[4]],
        )