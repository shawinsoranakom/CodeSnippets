def test_intersection(self):
        "Testing intersects() and intersection()."
        for topology_geom, intersect_geom in zip(
            self.geometries.topology_geoms, self.geometries.intersect_geoms
        ):
            a = fromstr(topology_geom.wkt_a)
            b = fromstr(topology_geom.wkt_b)
            i1 = fromstr(intersect_geom.wkt)
            i2 = a.intersection(b)
            with self.subTest(topology_geom=topology_geom):
                self.assertIs(a.intersects(b), True)
                self.assertTrue(i1.equals(i2))
                self.assertTrue(i1.equals(a & b))  # __and__ is intersection operator
                a &= b  # testing __iand__
                self.assertTrue(i1.equals(a))