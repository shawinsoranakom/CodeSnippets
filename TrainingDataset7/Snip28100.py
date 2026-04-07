def test_index_lookup(self):
        obj = NullableJSONModel.objects.create(value=["a", "b", None, 3])
        self.assertSequenceEqual(
            NullableJSONModel.objects.filter(value__2=JSONNull()), [obj]
        )
        self.assertSequenceEqual(NullableJSONModel.objects.filter(value__2=None), [obj])