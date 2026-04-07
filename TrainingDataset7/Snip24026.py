def test_linestring(self):
        "Testing LineString objects."
        prev = OGRGeometry("POINT(0 0)")
        for ls in self.geometries.linestrings:
            linestr = OGRGeometry(ls.wkt)
            self.assertEqual(2, linestr.geom_type)
            self.assertEqual("LINESTRING", linestr.geom_name)
            self.assertEqual(ls.n_p, linestr.point_count)
            self.assertEqual(ls.coords, linestr.tuple)
            self.assertEqual(linestr, OGRGeometry(ls.wkt))
            self.assertNotEqual(linestr, prev)
            msg = "Index out of range when accessing points of a line string: %s."
            with self.assertRaisesMessage(IndexError, msg % len(linestr)):
                linestr.__getitem__(len(linestr))
            prev = linestr

            # Testing the x, y properties.
            x = [tmpx for tmpx, tmpy in ls.coords]
            y = [tmpy for tmpx, tmpy in ls.coords]
            self.assertEqual(x, linestr.x)
            self.assertEqual(y, linestr.y)