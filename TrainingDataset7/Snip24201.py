def test_intersection(self):
        geom = Point(5, 23, srid=4326)
        qs = Country.objects.annotate(inter=functions.Intersection("mpoly", geom))
        for c in qs:
            if connection.features.empty_intersection_returns_none:
                self.assertIsNone(c.inter)
            else:
                self.assertIs(c.inter.empty, True)