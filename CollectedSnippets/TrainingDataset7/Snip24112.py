def test_read_mode_error(self):
        # Open raster in read mode
        rs = GDALRaster(self.rs_path, write=False)
        band = rs.bands[0]
        self.addCleanup(self._remove_aux_file)

        # Setting attributes in write mode raises exception in the _flush
        # method
        with self.assertRaises(GDALException):
            setattr(band, "nodata_value", 10)