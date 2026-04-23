def test_unbounded(self):
        r = NumericRange(None, None, "()")
        instance = RangesModel(decimals=r)
        instance.save()
        loaded = RangesModel.objects.get()
        self.assertEqual(r, loaded.decimals)