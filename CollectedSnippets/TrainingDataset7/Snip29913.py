def test_empty(self):
        r = NumericRange(empty=True)
        instance = RangesModel(ints=r)
        instance.save()
        loaded = RangesModel.objects.get()
        self.assertEqual(r, loaded.ints)