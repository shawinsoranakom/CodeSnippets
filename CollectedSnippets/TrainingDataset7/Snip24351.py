def test_multipolygons(self):
        "Testing MultiPolygon objects."
        fromstr("POINT (0 0)")
        for mp in self.geometries.multipolygons:
            mpoly = fromstr(mp.wkt)
            with self.subTest(mp=mp):
                self.assertEqual(mpoly.geom_type, "MultiPolygon")
                self.assertEqual(mpoly.geom_typeid, 6)
                self.assertEqual(mpoly.dims, 2)
                self.assertEqual(mp.valid, mpoly.valid)

                if mp.valid:
                    mpoly_len = len(mpoly)
                    self.assertEqual(mp.num_geom, mpoly.num_geom)
                    self.assertEqual(mp.n_p, mpoly.num_coords)
                    self.assertEqual(mp.num_geom, mpoly_len)
                    msg = f"invalid index: {mpoly_len}"
                    with self.assertRaisesMessage(IndexError, msg):
                        mpoly.__getitem__(mpoly_len)
                    for p in mpoly:
                        self.assertEqual(p.geom_type, "Polygon")
                        self.assertEqual(p.geom_typeid, 3)
                        self.assertIs(p.valid, True)
                    self.assertEqual(
                        mpoly.wkt,
                        MultiPolygon(*tuple(poly.clone() for poly in mpoly)).wkt,
                    )