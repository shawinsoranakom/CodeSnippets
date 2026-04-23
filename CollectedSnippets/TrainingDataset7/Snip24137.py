def test_gdal_full_version(self):
        full_version = gdal_full_version()
        self.assertIn(gdal_version(), full_version)
        self.assertTrue(full_version.startswith(b"GDAL"))