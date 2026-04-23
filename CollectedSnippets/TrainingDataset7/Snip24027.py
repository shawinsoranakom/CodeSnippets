def test_multilinestring(self):
        "Testing MultiLineString objects."
        prev = OGRGeometry("POINT(0 0)")
        for mls in self.geometries.multilinestrings:
            mlinestr = OGRGeometry(mls.wkt)
            self.assertEqual(5, mlinestr.geom_type)
            self.assertEqual("MULTILINESTRING", mlinestr.geom_name)
            self.assertEqual(mls.n_p, mlinestr.point_count)
            self.assertEqual(mls.coords, mlinestr.tuple)
            self.assertEqual(mlinestr, OGRGeometry(mls.wkt))
            self.assertNotEqual(mlinestr, prev)
            prev = mlinestr
            for ls in mlinestr:
                self.assertEqual(2, ls.geom_type)
                self.assertEqual("LINESTRING", ls.geom_name)
            msg = "Index out of range when accessing geometry in a collection: %s."
            with self.assertRaisesMessage(IndexError, msg % len(mlinestr)):
                mlinestr.__getitem__(len(mlinestr))