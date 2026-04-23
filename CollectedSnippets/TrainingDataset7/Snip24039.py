def test_union(self):
        "Testing union()."
        for i in range(len(self.geometries.topology_geoms)):
            a = OGRGeometry(self.geometries.topology_geoms[i].wkt_a)
            b = OGRGeometry(self.geometries.topology_geoms[i].wkt_b)
            u1 = OGRGeometry(self.geometries.union_geoms[i].wkt)
            u2 = a.union(b)
            self.assertTrue(u1.geos.equals(u2.geos))
            self.assertTrue(u1.geos.equals((a | b).geos))  # __or__ is union operator
            a |= b  # testing __ior__
            self.assertTrue(u1.geos.equals(a.geos))