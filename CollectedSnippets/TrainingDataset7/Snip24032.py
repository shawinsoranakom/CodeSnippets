def test_multipolygons(self):
        "Testing MultiPolygon objects."
        OGRGeometry("POINT(0 0)")
        for mp in self.geometries.multipolygons:
            mpoly = OGRGeometry(mp.wkt)
            self.assertEqual(6, mpoly.geom_type)
            self.assertEqual("MULTIPOLYGON", mpoly.geom_name)
            if mp.valid:
                self.assertEqual(mp.n_p, mpoly.point_count)
                self.assertEqual(mp.num_geom, len(mpoly))
                msg = "Index out of range when accessing geometry in a collection: %s."
                with self.assertRaisesMessage(IndexError, msg % len(mpoly)):
                    mpoly.__getitem__(len(mpoly))
                for p in mpoly:
                    self.assertEqual("POLYGON", p.geom_name)
                    self.assertEqual(3, p.geom_type)
            self.assertEqual(mpoly.wkt, OGRGeometry(mp.wkt).wkt)