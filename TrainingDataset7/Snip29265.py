def test_assign_o2o_id_none(self):
        b = UndergroundBar.objects.create(place=self.p1)
        b.place_id = None
        b.save()
        self.assertIsNone(b.place_id)
        self.assertFalse(UndergroundBar.place.is_cached(b))
        self.assertIsNone(b.place)
        self.assertTrue(UndergroundBar.place.is_cached(b))