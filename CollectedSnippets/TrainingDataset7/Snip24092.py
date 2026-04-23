def test_vsi_raster_creation(self):
        # Open a raster as a file object.
        with open(self.rs_path, "rb") as dat:
            # Instantiate a raster from the file binary buffer.
            vsimem = GDALRaster(dat.read())
        # The data of the in-memory file is equal to the source file.
        result = vsimem.bands[0].data()
        target = self.rs.bands[0].data()
        if numpy:
            result = result.flatten().tolist()
            target = target.flatten().tolist()
        self.assertEqual(result, target)