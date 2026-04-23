def test_measure_is_measure_and_set_measure(self):
        geom = OGRGeometry("POINT (1 2 3)")
        self.assertIs(geom.is_measured, False)
        geom.set_measured(True)
        self.assertIs(geom.is_measured, True)
        self.assertEqual(geom.wkt, "POINT ZM (1 2 3 0)")
        geom.set_measured(False)
        self.assertIs(geom.is_measured, False)
        self.assertEqual(geom.wkt, "POINT (1 2 3)")
        msg = "Input to 'set_measured' must be a boolean, got 'None'"
        with self.assertRaisesMessage(ValueError, msg):
            geom.set_measured(None)