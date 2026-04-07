def test_linearring(self):
        "Testing LinearRing objects."
        prev = OGRGeometry("POINT(0 0)")
        for rr in self.geometries.linearrings:
            lr = OGRGeometry(rr.wkt)
            # self.assertEqual(101, lr.geom_type.num)
            self.assertEqual("LINEARRING", lr.geom_name)
            self.assertEqual(rr.n_p, len(lr))
            self.assertEqual(lr, OGRGeometry(rr.wkt))
            self.assertNotEqual(lr, prev)
            prev = lr