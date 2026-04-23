def test_bulk_update(self):
        obj1 = NullableJSONModel.objects.create(value={"k": "1st"})
        obj2 = NullableJSONModel.objects.create(value={"k": "2nd"})
        obj1.value = JSONNull()
        obj2.value = JSONNull()
        NullableJSONModel.objects.bulk_update([obj1, obj2], fields=["value"])
        self.assertSequenceEqual(
            NullableJSONModel.objects.filter(value=JSONNull()),
            [obj1, obj2],
        )