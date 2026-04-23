def test_rs_srs(self):
        self.assertEqual(self.rs.srs.srid, 3086)
        self.assertEqual(self.rs.srs.units, (1.0, "metre"))