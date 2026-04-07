def test_multilinestring(self):
        "Testing MultiLineString objects."
        prev = fromstr("POINT(0 0)")
        for line in self.geometries.multilinestrings:
            ml = fromstr(line.wkt)
            with self.subTest(line=line):
                self.assertEqual(ml.geom_type, "MultiLineString")
                self.assertEqual(ml.geom_typeid, 5)
                self.assertEqual(ml.dims, 1)

                self.assertAlmostEqual(line.centroid[0], ml.centroid.x, 9)
                self.assertAlmostEqual(line.centroid[1], ml.centroid.y, 9)

                self.assertEqual(ml, fromstr(line.wkt))
                self.assertIs(ml == prev, False)  # Use assertIs() to test __eq__.
                prev = ml

                for ls in ml:
                    self.assertEqual(ls.geom_type, "LineString")
                    self.assertEqual(ls.geom_typeid, 1)
                    self.assertIs(ls.empty, False)

                ml_len = len(ml)
                msg = f"invalid index: {ml_len}"
                with self.assertRaisesMessage(IndexError, msg):
                    ml.__getitem__(ml_len)
                self.assertEqual(
                    ml.wkt, MultiLineString(*tuple(s.clone() for s in ml)).wkt
                )
                self.assertEqual(
                    ml, MultiLineString(*tuple(LineString(s.tuple) for s in ml))
                )