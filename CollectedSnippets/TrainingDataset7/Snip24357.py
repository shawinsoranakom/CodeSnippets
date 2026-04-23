def test_unary_union(self):
        "Testing unary_union."
        for topology_geom, union_geom in zip(
            self.geometries.topology_geoms, self.geometries.union_geoms
        ):
            a = fromstr(topology_geom.wkt_a)
            b = fromstr(topology_geom.wkt_b)
            u1 = fromstr(union_geom.wkt)
            u2 = GeometryCollection(a, b).unary_union
            with self.subTest(topology_geom=topology_geom):
                self.assertTrue(u1.equals(u2))