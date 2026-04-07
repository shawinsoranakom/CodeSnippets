def test_set_nodata_value_on_raster_creation(self):
        # Create raster filled with nodata values.
        rast = GDALRaster(
            {
                "datatype": 1,
                "width": 2,
                "height": 2,
                "srid": 4326,
                "bands": [{"nodata_value": 23}],
            }
        )
        # Get array from raster.
        result = rast.bands[0].data()
        if numpy:
            result = result.flatten().tolist()
        # All band data is equal to nodata value.
        self.assertEqual(result, [23] * 4)