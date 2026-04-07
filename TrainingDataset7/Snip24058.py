def test_is_3d_and_set_3d(self):
        geom = OGRGeometry("POINT (1 2)")
        self.assertIs(geom.is_3d, False)
        geom.set_3d(True)
        self.assertIs(geom.is_3d, True)
        self.assertEqual(geom.wkt, "POINT (1 2 0)")
        geom.set_3d(False)
        self.assertIs(geom.is_3d, False)
        self.assertEqual(geom.wkt, "POINT (1 2)")
        msg = "Input to 'set_3d' must be a boolean, got 'None'"
        with self.assertRaisesMessage(ValueError, msg):
            geom.set_3d(None)