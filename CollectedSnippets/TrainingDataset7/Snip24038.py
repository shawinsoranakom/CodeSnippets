def test_symdifference(self):
        "Testing sym_difference()."
        for i in range(len(self.geometries.topology_geoms)):
            a = OGRGeometry(self.geometries.topology_geoms[i].wkt_a)
            b = OGRGeometry(self.geometries.topology_geoms[i].wkt_b)
            d1 = OGRGeometry(self.geometries.sdiff_geoms[i].wkt)
            d2 = a.sym_difference(b)
            self.assertTrue(d1.geos.equals(d2.geos))
            self.assertTrue(
                d1.geos.equals((a ^ b).geos)
            )  # __xor__ is symmetric difference operator
            a ^= b  # testing __ixor__
            self.assertTrue(d1.geos.equals(a.geos))