def test_null_handling(self):
        NullableUUIDModel.objects.create(field=None)
        loaded = NullableUUIDModel.objects.get()
        self.assertIsNone(loaded.field)