def test_filter_in(self):
        obj = NullableJSONModel.objects.create(value=JSONNull())
        obj2 = NullableJSONModel.objects.create(value=[1])
        self.assertSequenceEqual(
            NullableJSONModel.objects.filter(value__in=[JSONNull(), [1], "foo"]),
            [obj, obj2],
        )