def test_tuple(self):
        instance = RangesModel(ints=(0, 10))
        instance.save()
        loaded = RangesModel.objects.get()
        self.assertEqual(NumericRange(0, 10), loaded.ints)