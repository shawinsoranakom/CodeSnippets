def test_difference(self):
        "Testing difference()."
        for topology_geom, union_geom in zip(
            self.geometries.topology_geoms, self.geometries.diff_geoms
        ):
            a = fromstr(topology_geom.wkt_a)
            b = fromstr(topology_geom.wkt_b)
            d1 = fromstr(union_geom.wkt)
            d2 = a.difference(b)
            with self.subTest(topology_geom=topology_geom):
                self.assertTrue(d1.equals(d2))
                self.assertTrue(d1.equals(a - b))  # __sub__ is difference operator
                a -= b  # testing __isub__
                self.assertTrue(d1.equals(a))