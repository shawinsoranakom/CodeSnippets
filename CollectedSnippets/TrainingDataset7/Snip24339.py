def test_multipoints(self):
        "Testing MultiPoint objects."
        for mp in self.geometries.multipoints:
            mpnt = fromstr(mp.wkt)
            with self.subTest(mp=mp):
                self.assertEqual(mpnt.geom_type, "MultiPoint")
                self.assertEqual(mpnt.geom_typeid, 4)
                self.assertEqual(mpnt.dims, 0)

                self.assertAlmostEqual(mp.centroid[0], mpnt.centroid.tuple[0], 9)
                self.assertAlmostEqual(mp.centroid[1], mpnt.centroid.tuple[1], 9)

                mpnt_len = len(mpnt)
                msg = f"invalid index: {mpnt_len}"
                with self.assertRaisesMessage(IndexError, msg):
                    mpnt.__getitem__(mpnt_len)
                self.assertEqual(mp.centroid, mpnt.centroid.tuple)
                self.assertEqual(mp.coords, tuple(m.tuple for m in mpnt))
                for p in mpnt:
                    self.assertEqual(p.geom_type, "Point")
                    self.assertEqual(p.geom_typeid, 0)
                    self.assertIs(p.empty, False)
                    self.assertIs(p.valid, True)