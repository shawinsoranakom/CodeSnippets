def test_vsi_buffer_property(self):
        # Create a vsi-based raster from scratch.
        rast = GDALRaster(
            {
                "name": "/vsimem/raster.tif",
                "driver": "tif",
                "width": 4,
                "height": 4,
                "srid": 4326,
                "bands": [
                    {
                        "data": range(16),
                    }
                ],
            }
        )
        # Do a round trip from raster to buffer to raster.
        result = GDALRaster(rast.vsi_buffer).bands[0].data()
        if numpy:
            result = result.flatten().tolist()
        # Band data is equal to nodata value except on input block of ones.
        self.assertEqual(result, list(range(16)))
        # The vsi buffer is None for rasters that are not vsi based.
        self.assertIsNone(self.rs.vsi_buffer)