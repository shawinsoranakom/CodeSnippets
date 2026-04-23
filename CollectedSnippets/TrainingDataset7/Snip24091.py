def test_nonexistent_file(self):
        msg = 'Unable to read raster source input "nonexistent.tif".'
        with self.assertRaisesMessage(GDALException, msg):
            GDALRaster("nonexistent.tif")