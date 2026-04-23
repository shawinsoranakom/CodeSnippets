def test_intersection(self):
        "Testing intersects() and intersection()."
        for i in range(len(self.geometries.topology_geoms)):
            a = OGRGeometry(self.geometries.topology_geoms[i].wkt_a)
            b = OGRGeometry(self.geometries.topology_geoms[i].wkt_b)
            i1 = OGRGeometry(self.geometries.intersect_geoms[i].wkt)
            self.assertTrue(a.intersects(b))
            i2 = a.intersection(b)
            self.assertTrue(i1.geos.equals(i2.geos))
            self.assertTrue(
                i1.geos.equals((a & b).geos)
            )  # __and__ is intersection operator
            a &= b  # testing __iand__
            self.assertTrue(i1.geos.equals(a.geos))