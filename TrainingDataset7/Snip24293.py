def test_values_srid(self):
        for c, v in zip(City.objects.all(), City.objects.values()):
            self.assertEqual(c.point.srid, v["point"].srid)