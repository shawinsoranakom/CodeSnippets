def test_nullable_o2o_delete(self):
        u = UndergroundBar.objects.create(place=self.p1)
        u.place_id = None
        u.save()
        self.p1.delete()
        self.assertTrue(UndergroundBar.objects.filter(pk=u.pk).exists())
        self.assertIsNone(UndergroundBar.objects.get(pk=u.pk).place)