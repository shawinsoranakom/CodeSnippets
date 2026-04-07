def test_vsi_invalid_buffer_error(self):
        msg = "Failed creating VSI raster from the input buffer."
        with self.assertRaisesMessage(GDALException, msg):
            GDALRaster(b"not-a-raster-buffer")