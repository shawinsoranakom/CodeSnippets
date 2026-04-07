def test_circularstring_has_linestring_features(self):
        geom = OGRGeometry("CIRCULARSTRING ZM (1 5 0 1, 6 2 0 2, 7 3 0 3)")
        self.assertIsInstance(geom, CircularString)
        self.assertEqual(geom.x, [1, 6, 7])
        self.assertEqual(geom.y, [5, 2, 3])
        self.assertEqual(geom.z, [0, 0, 0])
        self.assertEqual(geom.m, [1, 2, 3])
        self.assertEqual(
            geom.tuple,
            ((1.0, 5.0, 0.0, 1.0), (6.0, 2.0, 0.0, 2.0), (7.0, 3.0, 0.0, 3.0)),
        )
        self.assertEqual(geom[0], (1, 5, 0, 1))
        self.assertEqual(len(geom), 3)