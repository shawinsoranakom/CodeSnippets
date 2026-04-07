def test_assign_o2o_id_value(self):
        b = UndergroundBar.objects.create(place=self.p1)
        b.place_id = self.p2.pk
        b.save()
        self.assertEqual(b.place_id, self.p2.pk)
        self.assertFalse(UndergroundBar.place.is_cached(b))
        self.assertEqual(b.place, self.p2)
        self.assertTrue(UndergroundBar.place.is_cached(b))
        # Reassigning the same value doesn't clear a cached instance.
        b.place_id = self.p2.pk
        self.assertTrue(UndergroundBar.place.is_cached(b))