def test08_angular_linear(self):
        "Testing the linear and angular units routines."
        for s in srlist:
            srs = SpatialReference(s.wkt)
            self.assertEqual(s.ang_name, srs.angular_name)
            self.assertEqual(s.lin_name, srs.linear_name)
            self.assertAlmostEqual(s.ang_units, srs.angular_units, 9)
            self.assertAlmostEqual(s.lin_units, srs.linear_units, 9)