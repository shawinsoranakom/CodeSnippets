def test_symdifference(self):
        "Testing sym_difference()."
        for topology_geom, sdiff_geom in zip(
            self.geometries.topology_geoms, self.geometries.sdiff_geoms
        ):
            a = fromstr(topology_geom.wkt_a)
            b = fromstr(topology_geom.wkt_b)
            d1 = fromstr(sdiff_geom.wkt)
            d2 = a.sym_difference(b)
            with self.subTest(topology_geom=topology_geom):
                self.assertTrue(d1.equals(d2))
                self.assertTrue(
                    d1.equals(a ^ b)
                )  # __xor__ is symmetric difference operator
                a ^= b  # testing __ixor__
                self.assertTrue(d1.equals(a))