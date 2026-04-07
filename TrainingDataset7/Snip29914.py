def test_null(self):
        instance = RangesModel(ints=None)
        instance.save()
        loaded = RangesModel.objects.get()
        self.assertIsNone(loaded.ints)