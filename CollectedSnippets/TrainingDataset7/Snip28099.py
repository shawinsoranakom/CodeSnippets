def test_key_transform_exact_filter(self):
        obj = NullableJSONModel.objects.create(value={"key": None})
        self.assertSequenceEqual(
            NullableJSONModel.objects.filter(value__key=JSONNull()),
            [obj],
        )
        self.assertSequenceEqual(
            NullableJSONModel.objects.filter(value__key=None), [obj]
        )