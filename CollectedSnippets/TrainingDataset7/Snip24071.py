def test_get_linear_geometry(self):
        geom = OGRGeometry("CIRCULARSTRING (-0.797 0.466,-0.481 0.62,-0.419 0.473)")
        linear = geom.get_linear_geometry()
        self.assertEqual(linear.geom_name, "LINESTRING")
        self.assertIs(linear.has_curve, False)