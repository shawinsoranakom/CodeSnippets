def test_points(self):
        "Testing Point objects."

        OGRGeometry("POINT(0 0)")
        for p in self.geometries.points:
            if not hasattr(p, "z"):  # No 3D
                pnt = OGRGeometry(p.wkt)
                self.assertEqual(1, pnt.geom_type)
                self.assertEqual("POINT", pnt.geom_name)
                self.assertEqual(p.x, pnt.x)
                self.assertEqual(p.y, pnt.y)
                self.assertEqual((p.x, p.y), pnt.tuple)