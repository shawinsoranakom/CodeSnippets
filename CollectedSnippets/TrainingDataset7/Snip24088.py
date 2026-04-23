def test_rs_bands(self):
        self.assertEqual(len(self.rs.bands), 1)
        self.assertIsInstance(self.rs.bands[0], GDALBand)