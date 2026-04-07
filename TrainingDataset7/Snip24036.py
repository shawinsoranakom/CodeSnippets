def test_difference(self):
        "Testing difference()."
        for i in range(len(self.geometries.topology_geoms)):
            a = OGRGeometry(self.geometries.topology_geoms[i].wkt_a)
            b = OGRGeometry(self.geometries.topology_geoms[i].wkt_b)
            d1 = OGRGeometry(self.geometries.diff_geoms[i].wkt)
            d2 = a.difference(b)
            self.assertTrue(d1.geos.equals(d2.geos))
            self.assertTrue(
                d1.geos.equals((a - b).geos)
            )  # __sub__ is difference operator
            a -= b  # testing __isub__
            self.assertTrue(d1.geos.equals(a.geos))