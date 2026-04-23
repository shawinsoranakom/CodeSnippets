def test_range_object_boundaries(self):
        r = NumericRange(0, 10, "[]")
        instance = RangesModel(decimals=r)
        instance.save()
        loaded = RangesModel.objects.get()
        self.assertEqual(r, loaded.decimals)
        self.assertIn(10, loaded.decimals)