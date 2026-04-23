def test_key_in(self):
        obj1 = NullableJSONModel.objects.create(value={"key": None})
        obj2 = NullableJSONModel.objects.create(value={"key": [1]})
        self.assertSequenceEqual(
            NullableJSONModel.objects.filter(value__key__in=[JSONNull(), [1], 0]),
            [obj1, obj2],
        )