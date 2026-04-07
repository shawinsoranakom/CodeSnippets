def test_gdal_version(self):
        if GDAL_VERSION:
            self.assertEqual(gdal_version(), ("%s.%s.%s" % GDAL_VERSION).encode())
        else:
            self.assertIn(b".", gdal_version())