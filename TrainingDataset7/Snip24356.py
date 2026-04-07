def test_union(self):
        "Testing union()."
        for topology_geom, union_geom in zip(
            self.geometries.topology_geoms, self.geometries.union_geoms
        ):
            a = fromstr(topology_geom.wkt_a)
            b = fromstr(topology_geom.wkt_b)
            u1 = fromstr(union_geom.wkt)
            u2 = a.union(b)
            with self.subTest(topology_geom=topology_geom):
                self.assertTrue(u1.equals(u2))
                self.assertTrue(u1.equals(a | b))  # __or__ is union operator
                a |= b  # testing __ior__
                self.assertTrue(u1.equals(a))